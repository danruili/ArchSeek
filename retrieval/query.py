from retrieval.fusion_query import fusion_query
from retrieval.query_preprocess import query_preprocess
from utils.app_types import CaseDatabase, QuerySet, RetrievalResult, DesignCase
from pathlib import Path
import pickle
from collections import OrderedDict
import logging
from typing import List, Tuple, Union, Literal, Dict


def load_database(database_folder_path: str) -> CaseDatabase:
    """
    Load the database
    """
    # load all pkl files from the database folder
    database_cases = OrderedDict()
    for pkl_file in Path(database_folder_path).glob("*.pkl"):
        try:
            with open(pkl_file, "rb") as f:
                case: DesignCase = pickle.load(f)
                case_idx = case.case_id
                database_cases[case_idx] = case
        except Exception as e:
            logging.error(f"Error loading {pkl_file}: {e}")
    return CaseDatabase(database_cases)


def query_handler(database: Union[str, CaseDatabase],
                  query: Union[str, QuerySet, None], 
                  selected_ids: List[int] = None,
                  **kwargs,
                  ) -> Tuple[List[RetrievalResult], QuerySet]:
    """
    Handle the query, return the retrieval results and the query set
    """
    # preprocess the query
    if isinstance(query, QuerySet):
        query_set = query
    elif isinstance(query, str):
        if query == "":
            query_set = QuerySet([],[])
        else:
            query_set = query_preprocess(query, selected_ids)
            logging.info(f"Query set: {query_set}")
    else:
        query_set = QuerySet([],[])

    # load the database
    if isinstance(database, str):
        database_folder_path = database
        database = load_database(database_folder_path)

    # query the database
    retrieval_results = fusion_query(database, query_set, **kwargs)

    # return the results
    return retrieval_results, query_set


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser(description="Query the database")
    parser.add_argument("--database", type=str, help="Path to the database folder", default="data/example_index")
    parser.add_argument("--query", type=str, help="The query string", default="red brick")
    args = parser.parse_args()
     # handle the query
    result = query_handler(args.database, args.query)
     # print the results
    print(result[:3])