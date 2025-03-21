from utils.app_types import QuerySet, EnrichedQuery, default_filter_weights
from typing import Dict
import numpy as np


def add_item_to_query_set(query_set: QuerySet, entry_dict: Dict, add_id: str) -> QuerySet:
    """
    Add an item to the query set
    """
    query_set.selected_ids.append(add_id)
    max_entry = entry_dict[str(add_id)]
    query_set.queries.append(EnrichedQuery(max_entry, 
                                           related_id=add_id, weights=default_filter_weights))
    query_set.weights.append(0.5)
    query_set.weights = list(np.array(query_set.weights) / np.sum(query_set.weights))
    return query_set

def remove_item_from_query_set(query_set: QuerySet, remove_id: int) -> QuerySet:
    """
    Remove an item from the query set
    """
    query_set.selected_ids.remove(remove_id)
    for query in query_set.queries:
        if query.related_id == remove_id:
            query_set.queries.remove(query)

    # normalize the weights
    query_set.weights = list(np.array(query_set.weights) / np.sum(query_set.weights))
    return query_set
