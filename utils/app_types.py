from typing import List, Dict, Any, Union, Literal, OrderedDict, Tuple, TypeAlias
from dataclasses import dataclass, field
import numpy as np
from pathlib import Path


AssetCategory = Literal['text', 'facade', 'interior',
                    'floorplan', 'section', 'detail', 'birdview', 'other']
TopicCategory = Literal['form', 'style', 'material usage', 'sense of feeling',
                        'relations to the surrounding context', 
                        'passive design techniques', 
                        'general design highlights']
default_filter_weights = {(category, topic): 1.0 for category in AssetCategory.__args__ for topic in TopicCategory.__args__}
empty_filter_weights = {(category, topic): None for category in AssetCategory.__args__ for topic in TopicCategory.__args__}

ItemFilter: TypeAlias = Tuple[AssetCategory, TopicCategory]
FilterWeight: TypeAlias = Dict[ItemFilter, float]

@dataclass
class BaseQuestion:
    theme: TopicCategory
    content: str = None

    def __hash__(self) -> int:
        return hash(self.content)
    
    def __str__(self) -> str:
        return self.content


@dataclass
class AssetItem:
    """
    Used in: (1) preparing the vision model call (2) storing the results
    """
    asset_path: str
    category: AssetCategory
    answers: OrderedDict[BaseQuestion, List[str]] = field(default_factory=OrderedDict)
    multi_modal_embedding: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'asset_path': str(self.asset_path),
            'category': self.category,
            'answers': {q.theme: a for q, a in self.answers.items()},
            'multi_modal_embedding': self.multi_modal_embedding,
        }
    
    @staticmethod
    def from_dict(item_dict: Dict[str, Any]):
        answers = OrderedDict({BaseQuestion(theme): item_dict['answers'][theme] for theme in item_dict['answers']})
        if 'multi_modal_embedding' not in item_dict:
            item_dict['multi_modal_embedding'] = []
        return AssetItem(Path(item_dict['asset_path']), item_dict['category'], answers, item_dict['multi_modal_embedding'])
    
@dataclass
class RawTextItem:
    asset_path: str
    raw_content: str
    chunked_content: List[str] = field(default_factory=list)
    category: AssetCategory = "text"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunked_content': self.chunked_content,
            'raw_content': self.raw_content,
            'asset_path': str(self.asset_path),
        }
    
    @staticmethod
    def from_dict(item_dict: Dict[str, Any]):
        return RawTextItem(Path(item_dict['asset_path']), item_dict['raw_content'], item_dict['chunked_content'])
    
@dataclass
class DesignCase:

    def __init__(self, case_id, name, folder_path, web_link, content):
        self.case_id = case_id
        self.name: str = name
        self.folder_path: str = folder_path
        self.web_link: str = web_link
        self.content: List[Union[AssetItem, RawTextItem]] = content

        # generated during preprocessing
        self.embeddings: np.ndarray = None
        self.multi_modal_embeddings: np.ndarray = None  # multimodal embeddings for the texts
        self.all_texts: List[str] = None     

    def to_dict(self) -> Dict[str, Any]:
        return {
            'case_id': self.case_id,
            'name': self.name,
            'folder_path': str(self.folder_path),
            'web_link': self.web_link,
            'content': [item.to_dict() for item in self.content],
        }
    
    @staticmethod
    def from_dict(case_dict: Dict[str, Any]):
        content = []
        for item_dict in case_dict['content']:
            if 'chunked_content' in item_dict:
                content.append(RawTextItem.from_dict(item_dict))
            else:
                content.append(AssetItem.from_dict(item_dict))
        return DesignCase(case_dict['case_id'], case_dict['name'], Path(case_dict['folder_path']), case_dict['web_link'], content)
    
    def get_all_text(self) -> List[str]:
        """
        Get all the text blocks from the case content.
        Meanwhile, generate the mapping from the content index to the embedding index.
        And the mapping from the embedding index to the (category, question) pair.
        """
        if not hasattr(self, 'emd_idx_to_filter'):
            self.emd_idx_to_filter: Dict[int, ItemFilter] = {} # value is (category, question) pair
        if not hasattr(self, 'content_to_emb_idx'):
            self.content_to_emb_idx: Dict[int, List[int]] = {}
        results = []
        for item_idx, item in enumerate(self.content):
            start_idx = len(results)
            if isinstance(item, RawTextItem):
                results.extend(item.chunked_content)
            else:
                for q in item.answers:
                    indices = [len(results) + i for i in range(len(item.answers[q]))]
                    results.extend(item.answers[q])
                    for idx in indices:
                        self.emd_idx_to_filter[idx] = (item.category, q.theme)
            self.content_to_emb_idx[item_idx] = list(range(start_idx, len(results)))
        self.all_texts = results
        return results
    
    def get_emb_weights(self, 
                        filter_weights: Dict[ItemFilter, float],
                        text_only: bool = False,
                        ) -> np.ndarray:
        """
        Get the mask for the embeddings
        """
        emb_weights = np.zeros(self.embeddings.shape[0], dtype=float)

        # Get the mask for the text
        if text_only:
            item_mask = [isinstance(item, RawTextItem) for item in self.content]
        else:
            item_mask = [1.0 for _ in self.content]
        for item_idx, mask in enumerate(item_mask):
            if not mask:
                emb_weights[self.content_to_emb_idx[item_idx]] = None

        # Get the mask for the filters
        for emb_idx, cat_top_pair in self.emd_idx_to_filter.items():
            category, topic = cat_top_pair
            if (category, topic) in filter_weights:
                emb_weights[emb_idx] = filter_weights[(category, topic)]
            else:
                emb_weights[emb_idx] = 0

        # get the mean of non-None and non-zero values
        mean_value = np.mean(emb_weights[emb_weights != 0])
        # fill the zero values with the mean
        emb_weights = np.where(emb_weights == 0, mean_value, emb_weights)

        # # fill the None values with the zero
        # emb_weights = np.where(emb_weights == None, 0, emb_weights)

        return emb_weights
    
    def look_up_content(self, emb_idx) -> Tuple[Union[RawTextItem, AssetItem], str]:
        for item_idx, emb_indices in self.content_to_emb_idx.items():
            if emb_idx in emb_indices:
                return self.content[item_idx], self.all_texts[emb_idx]
        return None
    
    def look_up_filter(self, emb_idx) -> ItemFilter:
        if emb_idx not in self.emd_idx_to_filter:
            return None, None
        return self.emd_idx_to_filter[emb_idx]
    
    def get_all_image_paths(self) -> List[str]:
        return [item.asset_path for item in self.content if isinstance(item, AssetItem)]
    
    def set_all_image_embeddings(self, embeddings: List[List[float]]):
        emb_idx = 0
        for item in self.content:
            if isinstance(item, AssetItem):
                item.multi_modal_embedding = embeddings[emb_idx]
                emb_idx += 1

    def get_all_image_embeddings(self) -> List[List[float]]:
        # if has no attribute mul_emb_idx_to_item, create it
        if not hasattr(self, 'mul_emb_idx_to_item'):
            self.mul_emb_idx_to_item: List[AssetItem] = []
        result = []
        for item in self.content:
            if isinstance(item, AssetItem) and item.category != 'text':
                result.append(item.multi_modal_embedding)
                self.mul_emb_idx_to_item.append(item)
        return result

    def look_up_image(self, multi_modal_emb_idx) -> AssetItem:
        return self.mul_emb_idx_to_item[multi_modal_emb_idx]

    
@dataclass
class CaseDatabase:
    cases: OrderedDict[str, DesignCase]
    

@dataclass
class EnrichedQuery:
    """
    Base text query instance with weights for each category
    """
    content: str
    weights: FilterWeight = field(default_factory=dict)
    related_id: str = None

    txt_embedding: List[float] = field(default_factory=list)
    txt_multi_modal_embedding: List[float] = field(default_factory=list)
    img_embedding: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'weights': {f'{category}_{topic}': weight for (category, topic), weight in self.weights.items()},
            'related_id': self.related_id,
        }
    
    @staticmethod
    def from_dict(query_dict: Dict[str, Any]):
        weights = {tuple(key.split('_')): value for key, value in query_dict['weights'].items()}
        return EnrichedQuery(query_dict['content'], weights=weights, related_id=query_dict['related_id'])

@dataclass
class QuerySet:
    """
    Query after the augmentation. It will be used for the retrieval.
    """
    queries: List[EnrichedQuery] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    image_path: str = None  # image input path used for web page display
    selected_ids: List[int] = field(default_factory=list)

    @staticmethod
    def from_dict(query_dict: Dict[str, Any]):
        queries = [EnrichedQuery.from_dict(q) for q in query_dict['queries']]
        weights = query_dict['weights']
        image_path = query_dict['image_path']
        selected_ids = query_dict.get('selected_ids', [])
        return QuerySet(queries, weights, image_path, selected_ids)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'queries': [q.to_dict() for q in self.queries],
            'weights': self.weights,
            'image_path': self.image_path,
            'selected_ids': self.selected_ids,
        }


@dataclass
class RetrievalResult:
    case_id: int
    name: str
    score: float
    url: str
    max_entry: str
    max_item: Union[RawTextItem, AssetItem]
    max_filter: ItemFilter
    raw_scores: List[float] = field(default_factory=list)

    def to_simp_dict(self) -> Dict[str, Any]:
        raw_score_dict = {f'score_{i}': score for i, score in enumerate(self.raw_scores)}
        filter_dict = {'asset_category': self.max_filter[0], 'topic_category': self.max_filter[1]}
        base_dict = {
            'case_id': self.case_id,
            'name': self.name,
            'score': self.score,
            'max_entry': self.max_entry,
        }
        return {**base_dict, **raw_score_dict, **filter_dict}
    
    def to_app_dict(self) -> Dict[str, Any]:
        filter_dict = {'asset_category': self.max_filter[0], 'topic_category': self.max_filter[1]}
        base_dict = {
            'case_id': self.case_id,
            'max_entry': self.max_entry,
        }
        return base_dict
