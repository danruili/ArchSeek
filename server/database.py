from typing import OrderedDict

# supported operations:
# update_or_insert(user_id, key, value)
# pop the oldest item when the size exceeds the limit
class NaiveDatabase:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.data = OrderedDict()

    def update_or_insert(self, user_id: str, key: str, value: str) -> None:
        if user_id not in self.data:
            if len(self.data) >= self.max_size:
                self.data.popitem(last=False)
            self.data[user_id] = {}
        self.data[user_id][key] = value

    def get(self, user_id: str, key: str) -> str:
        return self.data.get(user_id, {}).get(key, None)
    