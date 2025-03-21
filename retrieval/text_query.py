from utils.app_types import CaseDatabase, EnrichedQuery, RetrievalResult, RawTextItem, DesignCase, FilterWeight, empty_filter_weights
from typing import List
import numpy as np

def text_based_query(
        database: CaseDatabase, 
        query: EnrichedQuery,
        text_only: bool = False,
        **kwargs
        ) -> List[RetrievalResult]:
    """
    Query the database, return unsorted retrieval results
    """
    retrieval_results = []

    query_embs = query.txt_embedding
    np_query_embs = np.array(query_embs)  # shape: (emb_dim, )

    for _, case_item in database.cases.items():
        weights = case_item.get_emb_weights(query.weights, text_only) # shape: (entry_count, )
        raw_dot_product = np.dot(case_item.embeddings, np_query_embs.T)  # shape: (entry_count,)
        dot_product = raw_dot_product * weights

        # concatenate the similarities
        max_dot_product = np.max(dot_product)
        max_item_idx = np.argmax(dot_product)
        max_item, max_entry = case_item.look_up_content(max_item_idx)
        item_filter = case_item.look_up_filter(max_item_idx)
        if isinstance(max_item, RawTextItem) or ("txt" in str(max_item.asset_path)):
            # use any image item for visualization
            for item in case_item.content:
                if "txt" not in str(item.asset_path):
                    max_item = item
                    break
        retrieval_results.append(
            RetrievalResult(case_item.case_id, case_item.name, max_dot_product, 
                            case_item.web_link,
                            max_entry, max_item, item_filter,
                            ))
        
    retrieval_results.sort(key=lambda x: x.score, reverse=True)
    return retrieval_results
    
