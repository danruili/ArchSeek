from typing import List, OrderedDict
import re
from retrying import retry
import json
import json5
from utils.app_types import BaseQuestion, AssetItem
from utils.llm import call_gpt_v, LLMHandler


IMAGE_PROMPT = """
you are a wonderful architecture critic. please describe the architectural design of this image in details. 

# Guide
- Cover the following aspects: 
{aspect_list}
- For each aspect, cover as many components as you can.
- Write like an architecture critic. 
- Your response should be in a structured json:
```json
{
  "analysis":{
    "form": [
        "<each sentence is a list item>",
    ],
    "<other aspects>": <return an empty list if not applicable>
  }
}
```
"""

TEXT_PROMPT = """
you are a wonderful architecture critic. Given the text input, please describe the architectural design in details. 

# Guide
- Cover the following aspects: 
{aspect_list}
- For each aspect, cover as many components as you can.
- Write like an architecture critic. 
- Your response should be in a structured json:
```json
{
  "analysis":{
    "form": [
        "<each sentence is a list item>",
    ],
    "<other aspects>": <return an empty list if not applicable>
  }
}
```

Your text:
{content}
"""

@retry(wait_fixed=2000, stop_max_attempt_number=3)
def image_inqury(image_path: str, 
                 questions: List[BaseQuestion],
                 ) -> AssetItem:
    
    # add a question
    questions.append(BaseQuestion("category", "Category of this image. Choose from: facade, interior, floorplan, section, detail, birdview, other"))

    # prepare the prompt
    question_str_list = []
    for q in questions:
        if q.content is not None:
            question_str_list.append(f"  - {q.theme}: {q.content}")
        else:
            question_str_list.append(f"  - {q.theme}")
    questionaire = "\n".join(question_str_list)
    prompt = IMAGE_PROMPT.replace("{aspect_list}", questionaire)

    # call the model
    response = call_gpt_v(image_path, prompt)
    json_text = re.findall(r'```json(.*)```', response, re.DOTALL)[-1]
    json_dict = json.loads(json_text)['analysis']

    # prepare the result
    answers = OrderedDict()
    for idx, item in enumerate(json_dict.items()):
        answers[questions[idx]] = item[1]
    category = json_dict["category"]
    if isinstance(category, list):
        category = category[0]
    del answers[questions[-1]] # remove the category question
    return AssetItem(str(image_path), category, answers)


@retry(wait_fixed=2000, stop_max_attempt_number=3)
def text_inquiry(text_path: str, 
                 questions: List[BaseQuestion],
                 ) -> AssetItem:
    
    # read the text file using utf-8 encoding
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read()

    # prepare the prompt
    question_str_list = []
    for q in questions:
        if q.content is not None:
            question_str_list.append(f"  - {q.theme}: {q.content}")
        else:
            question_str_list.append(f"  - {q.theme}")
    questionaire = "\n".join(question_str_list)
    prompt = TEXT_PROMPT.replace("{aspect_list}", questionaire)\
        .replace("{content}", text)

    # call the model
    llm_handler = LLMHandler()
    response = llm_handler.chat_with_gpt(prompt)
    json_text = re.findall(r'```json(.*)```', response, re.DOTALL)[-1]
    json_dict = json5.loads(json_text)["analysis"]

    # prepare the result
    answers = OrderedDict()
    for idx, item in enumerate(json_dict.items()):
        answers[questions[idx]] = item[1]
    return AssetItem(str(text_path), "text", answers)



if __name__ == "__main__":
    questions = [BaseQuestion("highlights", "What is the highlight of this design?"),
                 BaseQuestion("shape", "What form does it use? "),
                 BaseQuestion("spatial design", "What is the highlight of its shape and form? "),
                 BaseQuestion("material design", "What is the highlight in its spatial and material design?"),
                 ]

    image_path = r"D:\Code\RecArch\static\database\China\Shanghai IAG Art Museum\detail.jpg"
    text_path = r"D:\Code\RecArch\static\database\China\Shanghai IAG Art Museum\description.txt"
    case_id = 1
    # result = image_inqury(image_path, questions, case_id)
    result = text_inquiry(text_path, questions, case_id)
    print(result)
