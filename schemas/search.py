from typing import List, Optional
from pydantic import BaseModel, Field


class SuperSearchRequest(BaseModel):
    content: str = Field(..., min_length=1)
    country: Optional[str] = Field(None, description="국가/지역/도시/섬/관광지")
    searchEngine: Optional[str] = None


class ThemeSearchRequest(BaseModel):
    theme: str = Field(..., min_length=1)
    country: Optional[str] = None
    searchEngine: Optional[str] = None


class TravelItem(BaseModel):
    title: str = Field(description="여행지 이름")
    content: str = Field(description="2~4문장 추천 이유/팁")
    location: str = Field(description="국가/도시/지역")
    sources: List[str] = Field(description="참고자료 링크 2~5개")


class TravelResponse(BaseModel):
    results: List[TravelItem]