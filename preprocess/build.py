from pathlib import Path
import logging
import json
import pickle
import uuid

from preprocess.case_inquiry import case_inquiry
from preprocess.case_embedding import create_embs
from utils.app_types import CaseDatabase, DesignCase

def project_folder_iterate(database_folder_path):
    """
    Iterate all project folder in the database folder
    """
    idx = -1
    # iterate all folders in the country folder
    database_folder_path = Path(database_folder_path)
    for project_folder in database_folder_path.iterdir():
        # if the item is a folder
        if project_folder.is_dir():
            idx += 1
            yield idx, project_folder


def build_database(source_folder_path: str, 
                   target_folder_path: str,
                   overwrite=False
                   )-> CaseDatabase:
    # create the target folder if not exists
    target_folder_path = Path(target_folder_path)
    if not target_folder_path.exists():
        target_folder_path.mkdir(parents=True, exist_ok=True)

    cases = []
    for _, project_folder in project_folder_iterate(source_folder_path):
        project_name = project_folder.name
        case_json_path = target_folder_path / f"{project_name}.json"
        case_pkl_path = target_folder_path / f"{project_name}.pkl"

        # skip if the case pkl exists
        if case_pkl_path.exists() and not overwrite:
            logging.info(f"Read {project_name} pkl")
            # read the case from pkl
            with open(case_pkl_path, "rb") as f:
                case = pickle.load(f)
            # append the case to the list
            cases.append(case)
            continue

        # if the case json exists, skip query and create embeddings
        if case_json_path.exists() and not overwrite:
            logging.info(f"Read {project_folder} json")
            # read the case from json
            with open(case_json_path, "r", encoding="utf-8") as f:
                case_dict = json.load(f)
            case = DesignCase.from_dict(case_dict)

            # create the embeddings
            case = create_embs(case)

            # save the case to pkl
            with open(case_pkl_path, "wb") as f:
                pickle.dump(case, f, protocol=pickle.HIGHEST_PROTOCOL)

            # append the case to the list
            cases.append(case)
            continue

        # build the case from scratch
        logging.info(f"Building for {project_folder}")
        case_id = str(uuid.uuid4())
        case = case_inquiry(case_id, project_folder)
        with open(case_json_path, "w", encoding="utf-8") as f:
            json.dump(case.to_dict(), f, indent=2)
        case = create_embs(case)
        
        with open(case_pkl_path, "wb") as f:
            pickle.dump(case, f, protocol=pickle.HIGHEST_PROTOCOL)
        cases.append(case)

    # create the database
    return CaseDatabase(cases)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/example_dataset")
    parser.add_argument("--output", type=str, default="data/example_index")
    parser.add_argument("--overwrite", type=bool, default=False)
    args = parser.parse_args()

    build_database(args.data, args.output, args.overwrite)
