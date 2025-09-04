from dataclasses import dataclass
from typing import Optional


@dataclass
class HospitalInfo:
    """
    Represents a hospital and its ranking metadata.
    """
    name: str
    specialty: Optional[str] = None
    exists: bool = False
    type: Optional[str] = None  # "public" or "private"
    ranking: Optional[int] = None

    def load_info(self, ranking_list: dict):
        """
        Load hospital info from a ranking list (dict).
        ranking_list[name] should contain {"type": ..., "ranking": ...}
        """
        record = ranking_list.get(self.name)
        if record:
            self.exists = True
            self.type = record.get("type")
            self.ranking = record.get("ranking")