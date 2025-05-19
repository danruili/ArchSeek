from retrieval.text_query import text_based_query
from retrieval.multi_modal_query import multi_modal_query
from utils.app_types import CaseDatabase, QuerySet, RetrievalResult, EnrichedQuery, DesignCase, AssetItem, ItemFilter, BaseQuestion
from typing import List, Literal, OrderedDict
import numpy as np
from copy import deepcopy
from utils.replicate_api import batch_text_embeddings
from utils.llm import LLMHandler


SearchMode = Literal["text", "image", "fusion", "random"]


def embed_query_set(query_set: QuerySet) -> QuerySet:
    """
    Embed the query set if it contains text content but no embedding
    If the query contains image embedding, do nothing
    """
    for query in query_set.queries:
        if not query.txt_embedding and query.content:
            # query.txt_multi_modal_embedding = np.array(batch_text_embeddings([query.content])[0])
            # query.txt_multi_modal_embedding = query.txt_multi_modal_embedding / np.linalg.norm(query.txt_multi_modal_embedding)
            query.txt_embedding = LLMHandler().get_text_embeddings(query.content)
    return query_set


def randomize_result(design_case: DesignCase) -> RetrievalResult:
    """
    Randomize the result for the design case
    """
    case_id = design_case.case_id
    case_name = design_case.name
    score = 0
    web_link = design_case.web_link
    # ramdomly choose an AssetItem from case.content
    while True:
        max_item = np.random.choice(design_case.content)
        if isinstance(max_item, AssetItem) and max_item.category != "text":
            answers: OrderedDict = max_item.answers
            while True:
                # randomly choose a topic from the answers
                question: BaseQuestion = np.random.choice(list(answers.keys()))
                max_filter: ItemFilter = (max_item.category, question.theme)
                answers_list = answers[question]
                if len(answers_list) > 0:
                    max_entry = np.random.choice(answers_list)
                    return RetrievalResult(case_id, case_name, score, web_link, max_entry, max_item, max_filter)


def fusion_query(database: CaseDatabase, 
                input_query_set: QuerySet,
                mode: SearchMode = "text",
                query_k: float = 10,
                **kwargs
                ) -> List[RetrievalResult]:
    if mode == "random" or len(input_query_set.queries) == 0:
        result_list = [randomize_result(case) for _, case in database.cases.items()]
        np.random.shuffle(result_list)
        return result_list
    else:
        query_set = deepcopy(input_query_set)
        query_set = embed_query_set(query_set)
        result_list = [text_img_fusion_query(database, query, mode, **kwargs) for query in query_set.queries]

        # calculate weighted rank score
        rank_scores = {}
        for query_idx, result in enumerate(result_list):
            for rank, item in enumerate(result):
                if item.case_id not in rank_scores:
                    rank_scores[item.case_id] = 0
                rank_scores[item.case_id] += 1 / (rank + query_k) * query_set.weights[query_idx]

        # sort the scores
        sorted_scores = sorted(rank_scores.items(), key=lambda x: x[1], reverse=True)

        final_result = []
        for case_id, score in sorted_scores:
            case = next(case for _, case in database.cases.items() if case.case_id == case_id)
            max_entry = next(item.max_entry for item in result_list[0] if item.case_id == case_id)
            max_item = next(item.max_item for item in result_list[0] if item.case_id == case_id)
            max_filter = next(item.max_filter for item in result_list[0] if item.case_id == case_id)

            final_result.append(RetrievalResult(
                case_id, case.name, score, case.web_link, max_entry, max_item, max_filter
            ))

        return final_result
 

def text_img_fusion_query(
        database: CaseDatabase,
        query: EnrichedQuery,
        mode: SearchMode = "fusion",
        **kwargs
        ) -> List[RetrievalResult]:
    if mode == "text":
        text_result = text_based_query(database, query, **kwargs)
        return text_result
    elif mode == "image":
        img_result = multi_modal_query(database, query, **kwargs)
        return img_result
    elif mode == "fusion":
        text_result = text_based_query(database, query, **kwargs)
        img_result = multi_modal_query(database, query, **kwargs)
        return rrf_fusion(database, text_result, img_result)


def rrf_fusion(database: CaseDatabase, 
               text_result: List[RetrievalResult],
               img_result: List[RetrievalResult],
               k: float = 10
               ) -> List[RetrievalResult]:
    # use RRF to fuse the results
    rank_in_text = {item.case_id: rank for rank, item in enumerate(text_result)}
    rank_in_img = {item.case_id: rank for rank, item in enumerate(img_result)}
    score_in_text = {item.case_id: item.score for item in text_result}
    score_in_img = {item.case_id: item.score for item in img_result}

    scores = {}
    for result in [text_result, img_result]:
        for rank, item in enumerate(result):
            if item.case_id not in scores:
                scores[item.case_id] = 0
            scores[item.case_id] += 1 / (rank + k)
            
    # sort the scores
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    final_result = []
    for case_id, score in sorted_scores:
        case = next(case for _, case in database.cases.items() if case.case_id == case_id)
        max_entry_in_text = next(item.max_entry for item in text_result if item.case_id == case_id)

        if case_id not in rank_in_img or rank_in_text[case_id] < rank_in_img[case_id]:
            max_item = next(item.max_item for item in text_result if item.case_id == case_id)
            max_filter = next(item.max_filter for item in text_result if item.case_id == case_id)
        else:
            max_item = next(item.max_item for item in img_result if item.case_id == case_id)
            max_filter = next(item.max_filter for item in img_result if item.case_id == case_id)

        final_result.append(RetrievalResult(
            case_id, case.name, score, case.web_link, max_entry_in_text, max_item, max_filter,
            raw_scores=[score_in_text.get(case_id, 0), score_in_img.get(case_id, 0)]
        ))
    return final_result

