from utils.app_types import RetrievalResult, QuerySet
from typing import List

def results_to_html_dict(results: List[RetrievalResult],
                         query_set: QuerySet,
                         ) -> dict:
    """
    Convert the results to a list of dictionaries for HTML rendering
    """
    results_list = []
    for result in results:
        path = str(result.max_item.asset_path)
        path = '/backend-api/img/'+path.split("data\\")[-1].replace("\\", "/")
        # keep 1 decimal places for the similarity score
        score = "{:.1f}".format(result.score * 100)
        results_list.append({
            'name': result.name,
            'similarity': score,
            'image_path': path,
            'web_url': result.url,
            'entry': result.max_entry[:200],
            'case_id': result.case_id,
            'category': result.max_filter[0],
            'topic': result.max_filter[1],
        })
    query_list = []
    for query, weight in zip(query_set.queries, query_set.weights):
        query_list.append({
            'query': query.content,
            'weight': weight,
        })
    selected_flags = [1 if result.case_id in query_set.selected_ids else 0 for result in results]
    return {"result": results_list, "query": query_list, "image_path": query_set.image_path, "selected": selected_flags}