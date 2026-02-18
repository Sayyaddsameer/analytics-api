from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Metric(BaseModel):
    timestamp: datetime
    value: float
    type: str = Field(..., description="Type of metric, e.g., cpu_usage")

class SummaryResponse(BaseModel):
    type: str
    period: str
    average_value: float
    count: int
    external_data: Optional[dict] = None