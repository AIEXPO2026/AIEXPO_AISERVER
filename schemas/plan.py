from pydantic import BaseModel, Field
from typing import List


class DailyPlanRequest(BaseModel):
    location: str = Field(..., description="여행 도시 또는 지역")
    start_time: str = Field(..., description="여행 시작 시간 예: 10:00")
    end_time: str = Field(..., description="여행 종료 시간 예: 18:00")


class PlanItem(BaseModel):
    time: str = Field(description="시간")
    activity: str = Field(description="활동 내용")


class DailyPlanResponse(BaseModel):
    plan: List[PlanItem]