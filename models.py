from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class LogEntry:
    timestamp: datetime
    domain: str
    email: str
    id: Optional[int] = None

@dataclass
class DomainList:
    domain: str
    list_type: str  # 'direct' or 'proxy'
    id: Optional[int] = None
