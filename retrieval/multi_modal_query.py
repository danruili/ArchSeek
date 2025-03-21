from utils.app_types import CaseDatabase, RetrievalResult, EnrichedQuery
from typing import List
import numpy as np


def multi_modal_query(
        database: CaseDatabase, 
        query: EnrichedQuery,
        **kwargs
        ) -> List[RetrievalResult]:
    """
    Query the database, return unsorted retrieval results
    """
    retrieval_results = []

    np_query_embs = query.txt_multi_modal_embedding # shape: (emb_dim, )

    for _, case_item in database.cases.items():
        img_embs = case_item.get_all_image_embeddings()
        if len(img_embs) == 0:
            continue
        img_embs = np.array(img_embs)  # shape: (entry_count, emb_dim)
        # normalize the length of the embeddings
        img_embs = img_embs / np.linalg.norm(img_embs, axis=1)[:, np.newaxis]
        raw_dot_product = np.dot(img_embs, np_query_embs.T)  # shape: (entry_count, )
        dot_product = raw_dot_product

        # concatenate the similarities
        max_dot_product = np.max(dot_product)
        max_item_idx = np.argmax(dot_product)
        max_item = case_item.look_up_image(max_item_idx)
        retrieval_results.append(
            RetrievalResult(case_item.case_id, case_item.name, max_dot_product, 
                            case_item.web_link,
                            "image match", max_item, (max_item.category, "image"),
                            None))
                
    retrieval_results.sort(key=lambda x: x.score, reverse=True)
    return retrieval_results
