from utils.app_types import DesignCase
from utils.llm import LLMHandler
from utils.replicate_api import batch_text_embeddings, batch_image_embeddings
import numpy as np

def create_embs(case: DesignCase) -> DesignCase:
    """
    Create embeddings for each asset in the case.
    """
    texts = case.get_all_text()
    # get the indices where the text is not empty or ""
    non_empty_indices = [i for i, text in enumerate(texts) if text != ""]
    # get the non empty texts
    non_empty_texts = [texts[i] for i in non_empty_indices]

    # get the embeddings
    emb_handler = LLMHandler()
    non_empty_embs = emb_handler.get_text_embeddings_multi(non_empty_texts)
    # create a list of empty embeddings
    embs = [np.zeros(len(non_empty_embs[0])) for _ in texts]
    # fill the embeddings with the non empty embeddings
    for i, emb in zip(non_empty_indices, non_empty_embs):
        embs[i] = emb
    case.embeddings = np.array(embs)

    # get multimodal embeddings
    non_empty_embs_multi = batch_text_embeddings(non_empty_texts, max_workers=6)
    embs_multi = [np.zeros(len(non_empty_embs_multi[-1])) for _ in texts]
    for i, emb in zip(non_empty_indices, non_empty_embs_multi):
        embs_multi[i] = emb
    case.multi_modal_embeddings = np.array(embs_multi)

    # get the image embeddings
    image_paths = case.get_all_image_paths()
    image_embs = batch_image_embeddings(image_paths, max_workers=8)
    case.set_all_image_embeddings(image_embs)

    return case
