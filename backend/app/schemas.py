from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    MD = "md"


class TaskStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    IDENTIFIED = "identified"
    COMPLETED = "completed"
    FAILED = "failed"


class DataType(str, Enum):
    NAME = "name"
    ID_CARD = "id_card"
    PHONE = "phone"
    ADDRESS = "address"
    BANK_CARD = "bank_card"
    EMAIL = "email"


class StrategyType(str, Enum):
    MASK = "mask"
    REPLACE = "replace"
    DELETE = "delete"


class TaskCreate(BaseModel):
    filename: str
    file_size: int
    file_type: FileType


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    file_size: int
    file_type: FileType
    upload_time: datetime
    status: TaskStatus


class SensitiveItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    type: DataType
    value: str
    start_pos: int
    end_pos: int
    confidence: float


class DesensitizationRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    data_type: DataType
    strategy: StrategyType
    enabled: bool


class PreviewRequest(BaseModel):
    rules: List[str]
    sensitive_items: Optional[List[str]] = None


class PreviewResponse(BaseModel):
    original: str
    desensitized: str
    statistics: Dict[str, int]


class ExportRequest(BaseModel):
    rules: List[str]
    output_format: FileType
