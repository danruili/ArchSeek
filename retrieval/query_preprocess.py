from utils.app_types import EnrichedQuery, QuerySet, BaseQuestion, default_filter_weights
from utils.llm import call_gpt_v, LLMHandler
from pathlib import Path
import logging
from retrying import retry
import json
import numpy as np
from typing import List, Tuple
import re


image_questions = [
    BaseQuestion("form"),
    BaseQuestion("style"),
    BaseQuestion("material usage"),
    BaseQuestion("sense of feeling"),
    BaseQuestion("relations to the surrounding context"),
]

QUERY_IMAGE_PROMPT = """
you are a wonderful architecture critic. please describe the architectural design of this image. 

# Guide
- Cover the following aspects: 
{aspect_list}
- Write like an architecture critic. 
- Your response should be in a structured json:
```json
{
  "analysis":{
    "form": {"content": "<your analysis here>", "weight": <weight of the analysis>},
    "<other aspects>": <return an empty dict if not applicable>
  }
}
```
"""


def enrich_query(raw_query: str, selected_ids: List[int], augment=False) -> QuerySet:
    """
    Enrich the query
    """
    if not augment:
        query = EnrichedQuery(raw_query, weights=default_filter_weights)
        return QuerySet([query], [1.0], selected_ids=selected_ids)
    else:
        raise NotImplementedError("Augmented query is not implemented yet.")



@retry(wait_fixed=2000, stop_max_attempt_number=3)
def image_inqury(image_path: str, 
                 questions: List[BaseQuestion],
                 ) -> Tuple[List[str], List[float]]:
    
    # prepare the prompt
    question_str_list = []
    for q in questions:
        if q.content is not None:
            question_str_list.append(f"  - {q.theme}: {q.content}")
        else:
            question_str_list.append(f"  - {q.theme}")
    questionaire = "\n".join(question_str_list)
    prompt = QUERY_IMAGE_PROMPT.replace("{aspect_list}", questionaire)

    # call the model
    response = call_gpt_v(image_path, prompt)
    json_text = re.findall(r'```json(.*)```', response, re.DOTALL)[-1]
    json_dict = json.loads(json_text)['analysis']

    # prepare the result
    queries = []
    weights = []
    for theme, item in json_dict.items():
        queries.append(item['content'])
        weights.append(float(item['weight']))

    # normalize the weights
    weights = np.array(weights)
    weights = weights / weights.sum()

    # convert the weights to a list
    weights = weights.tolist()

    return queries, weights

@retry(wait_fixed=5000, stop_max_attempt_number=3)
def query_preprocess(query: str, selected_ids: List[int] = None) -> QuerySet:
    """
    Handle the query
    """
    if selected_ids is None:
        selected_ids = []

    # check if the query is a file path to an image
    if Path(query).exists():
        logging.info("Query recognized as an image file path")

        # get the text description of the image
        query_str_list, weight_list = image_inqury(query, image_questions)
        queries = []
        for query_str in query_str_list:
            enriched_query = EnrichedQuery(query_str, weights=default_filter_weights)
            queries.append(enriched_query)

        # copy the image to the temp folder
        # create temp folder if not exists
        Path("temp").mkdir(parents=True, exist_ok=True)
        # copy the image to the temp folder
        source_path = Path(query)
        dest_path = Path(f"temp/{Path(query).name}")
        dest_path.write_bytes(source_path.read_bytes())
        return QuerySet(queries, weight_list, image_path=str(dest_path), selected_ids=selected_ids)
            
    else:
        logging.info("Query recognized as a text")
        query_str = query

        # enrich the query
        query_set = enrich_query(query_str, selected_ids)
        return query_set