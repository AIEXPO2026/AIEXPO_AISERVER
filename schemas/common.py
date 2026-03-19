from typing import List, Optional
from pydantic import BaseModel, Field


class CourseRequest(BaseModel):
    location: str = Field(..., description="현재 위치 또는 시작 여행지 예: 후쿠오카 타워")


class CourseSaveRequest(BaseModel):
    nickname: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1, description="현재 위치 또는 시작 여행지")


class TravelContextRequest(BaseModel):
    moods: List[int] = Field(default_factory=list)
    peopleCounts: List[int] = Field(default_factory=list)
    avgWeathers: List[str] = Field(default_factory=list)
    budgetMin: Optional[int] = None
    budgetMax: Optional[int] = None


class CustomizeCourseRequest(BaseModel):
    style: str = Field(..., description="감성 / 힐링 / 혼행 / 액티비티 / 맛집")
    savedPlaces: List[str] = Field(default_factory=list)
    travelContext: Optional[TravelContextRequest] = None


class CourseItem(BaseModel):
    order: int = Field(description="방문 순서")
    place: str = Field(description="장소 이름")


class CourseResponse(BaseModel):
    course: List[CourseItem]