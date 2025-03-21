import os
from pathlib import Path
from utils.app_types import DesignCase, BaseQuestion, TopicCategory
from preprocess.asset_inquiry import image_inqury, text_inquiry
from preprocess.asset_text_process import split_text


text_questions = [BaseQuestion(question) for question in list(TopicCategory.__args__)]
image_questions = [BaseQuestion(question) for question in list(TopicCategory.__args__)]

def case_inquiry(case_id,
                 case_folder_path:str,
                 ) -> DesignCase:
    
    # get case name from the folder name
    case_name = Path(case_folder_path).name

    # get web link from the meta.csv
    meta_csv_path = Path(case_folder_path) / "meta.csv"
    web_url = ""
    if meta_csv_path.exists():
        with open(meta_csv_path, "r") as f:
            meta = f.readline().split(",")
            if len(meta) > 1:
                web_url = meta[1]

    # initialize the assets
    assets = []
    
    # get the text file path
    text_path = Path(case_folder_path) / "description.txt"
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"{text_path} does not exist.")
    
    # chunk and add the text asset
    text_result = split_text(text_path)
    assets.append(text_result)

    # call the text inquiry
    text_result = text_inquiry(text_path, text_questions)
    assets.append(text_result)

    # iterate all jpg files in the folder
    for image_path in Path(case_folder_path).glob("*.jpg"):
        questions = image_questions

        # call the image inquiry
        image_result = image_inqury(image_path, questions)
        assets.append(image_result)

    return DesignCase(case_id, case_name, str(case_folder_path), 
                      web_url, assets)


if __name__ == "__main__":
    case_id = 1
    case_folder_path = r"data\example_dataset\Vyborg Library"
    case = case_inquiry(case_id, case_folder_path)
    print(case.to_dict())