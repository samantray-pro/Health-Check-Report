from typing import List, Optional
from pydantic import BaseModel

class ProfileCreate(BaseModel):
    name: str
    age: int
    gender: str
    health_issues: Optional[str] = ""

class TestRecordItem(BaseModel):
    test_name: str
    raw_test_name: Optional[str] = None
    value: float
    unit: Optional[str] = ""
    reference_range: Optional[str] = ""
    flag: Optional[str] = "NORMAL"

class ConfirmReportPayload(BaseModel):
    test_date: str
    filename: Optional[str] = "Manual Entry"
    file_path: Optional[str] = ""
    records: List[TestRecordItem]
