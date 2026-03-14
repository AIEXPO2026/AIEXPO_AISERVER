import os
from typing import List, Optional, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Cambodia AI Server", version="1.4.0")


class SuperSearchRequest(BaseModel):
    content: str = Field(..., min_length=1)
    country: str = Field(..., min_length=1, description="국가/지역/도시/섬/관광지")
    searchEngine: str = Field(..., min_length=1)


class ThemeSearchRequest(BaseModel):
    theme: str = Field(..., min_length=1)
    country: Optional[str] = None
    searchEngine: Optional[str] = None


class CourseRequest(BaseModel):
    location: str = Field(..., description="현재 위치 또는 시작 여행지 예: 후쿠오카 타워")


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


class DailyPlanRequest(BaseModel):
    location: str = Field(..., description="여행 도시 또는 지역")
    start_time: str = Field(..., description="여행 시작 시간 예: 10:00")
    end_time: str = Field(..., description="여행 종료 시간 예: 18:00")


class TravelItem(BaseModel):
    title: str = Field(description="여행지 이름")
    content: str = Field(description="2~4문장 추천 이유/팁")
    location: str = Field(description="국가/도시/지역")
    sources: List[str] = Field(description="참고자료 링크 2~5개")


class TravelResponse(BaseModel):
    results: List[TravelItem]


class PlanItem(BaseModel):
    time: str = Field(description="시간")
    activity: str = Field(description="활동 내용")


class DailyPlanResponse(BaseModel):
    plan: List[PlanItem]


class CourseItem(BaseModel):
    order: int = Field(description="방문 순서")
    place: str = Field(description="장소 이름")


class CourseResponse(BaseModel):
    course: List[CourseItem]


class SearchEngineItem(BaseModel):
    code: str
    label: str


class SearchEngineListResponse(BaseModel):
    country: str
    engines: List[SearchEngineItem]


parser = JsonOutputParser(pydantic_object=TravelResponse)
daily_parser = JsonOutputParser(pydantic_object=DailyPlanResponse)
course_parser = JsonOutputParser(pydantic_object=CourseResponse)

llm = ChatOpenAI(
    model="gpt-5.4",
    temperature=0.3,
    api_key=OPENAI_API_KEY,
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            너는 여행지 추천 AI다.
            반드시 지정된 JSON 형식으로만 응답해야 한다.

            조건:
            - 여행지 최대 5개
            - sources는 2~5개
            - 공식/권위/대형 가이드/공공기관/유네스코 우선
            - 사용자의 요청, 여행 대상 지역, 검색엔진 성향을 반영할 것
            - 근거 없는 과장 금지
            - 사용자가 입력한 여행 대상 범위를 절대 벗어나지 말 것
            - 입력값이 국가가 아니라 지역, 도시, 섬, 관광지여도 그대로 해당 범위 안에서만 추천할 것
            - 예를 들어 독도가 입력되면 서울, 부산, 제주처럼 먼 지역은 절대 추천하지 말 것
            - 추천 가능한 장소가 적은 좁은 지역이면 같은 범위 안에서 세부 스팟, 관람 포인트, 방문 방식, 시간대 추천으로 구성할 것
            - 입력 범위를 억지로 더 큰 행정구역 전체로 확장하지 말 것

            {format_instructions}
            """,
        ),
        ("user", "{user_input}"),
    ]
)

daily_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            너는 여행 일정 생성 AI다.
            하루 여행 일정을 시간 기반으로 만들어라.

            규칙:
            - 시간 순서로 정렬
            - 장소 이동을 고려한 자연스러운 일정
            - 너무 촘촘하지 않게 구성
            - 점심 식사 포함
            - 반드시 JSON 형식으로만 응답

            {format_instructions}
            """,
        ),
        ("user", "{user_input}"),
    ]
)

course_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            너는 위치 기반 여행 코스 생성 AI다.
            사용자가 입력한 현재 위치 또는 시작 여행지를 기준으로,
            일반적인 관광 동선과 대표 명소를 참고해서 자연스러운 여행 코스를 만들어라.

            규칙:
            - 방문 순서는 1부터 시작
            - 현재 위치와 가까운 장소부터 자연스럽게 이어지도록 구성
            - 중복 장소 금지
            - course는 최대 4개로 구성
            - 반드시 JSON 형식으로 응답

            {format_instructions}
            """,
        ),
        ("user", "{user_input}"),
    ]
)

customize_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            너는 여행 코스 맞춤 설정 AI다.
            특정 사용자가 기존에 저장한 여행 코스 데이터를 참고해서
            사용자가 선택한 스타일에 맞는 개인별 맞춤 코스를 재구성해라.

            규칙:
            - 해당 사용자의 저장 데이터를 최대한 활용
            - 스타일에 맞게 순서를 재배치
            - 감성 / 힐링 / 혼행 / 액티비티 / 맛집 중 하나를 반영
            - 방문 순서는 1부터 시작
            - 중복 장소 금지
            - course는 최대 4개로 구성
            - 반드시 JSON 형식으로 응답

            {format_instructions}
            """,
        ),
        ("user", "{user_input}"),
    ]
)

COUNTRY_SEARCH_ENGINES: Dict[str, List[Dict[str, str]]] = {
    "대한민국": [
        {"code": "naver", "label": "네이버"},
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "일본": [
        {"code": "google", "label": "구글"},
        {"code": "yahoo", "label": "야후 재팬"},
        {"code": "bing", "label": "빙"},
    ],
    "미국": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
        {"code": "duckduckgo", "label": "덕덕고"},
    ],
    "대만": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "태국": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "프랑스": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
}

DEFAULT_ENGINES = [
    {"code": "google", "label": "구글"},
    {"code": "bing", "label": "빙"},
]


def run_chain(user_input: str):
    chain = prompt_template | llm | parser
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": parser.get_format_instructions(),
    })


def run_daily_plan_chain(user_input: str):
    chain = daily_prompt_template | llm | daily_parser
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": daily_parser.get_format_instructions(),
    })


def run_course_chain(user_input: str):
    chain = course_prompt_template | llm | course_parser
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": course_parser.get_format_instructions(),
    })


def run_customize_course_chain(user_input: str):
    chain = customize_prompt_template | llm | course_parser
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": course_parser.get_format_instructions(),
    })


def get_country_engines(country: str) -> List[Dict[str, str]]:
    return COUNTRY_SEARCH_ENGINES.get(country, DEFAULT_ENGINES)


def get_search_engine_style(search_engine: str) -> str:
    if search_engine == "naver":
        return "로컬 인기 스팟과 맛집 중심"
    if search_engine == "google":
        return "대표 관광지와 랜드마크 중심"
    if search_engine == "bing":
        return "감성적인 명소와 사진 스팟 중심"
    if search_engine == "yahoo":
        return "대중적인 관광지와 지역 명소 중심"
    if search_engine == "duckduckgo":
        return "균형 잡힌 탐색형 추천"
    return "균형 잡힌 여행지 추천"


@app.get("/search/engines", response_model=SearchEngineListResponse)
async def search_engines(country: str = Query(..., min_length=1)):
    engines = get_country_engines(country)
    return {
        "country": country,
        "engines": engines,
    }


@app.post("/search/super")
async def super_search(req: SuperSearchRequest):
    try:
        style_hint = get_search_engine_style(req.searchEngine)

        user_prompt = f"""
        사용자 요청:
        {req.content}

        여행 대상:
        {req.country}

        사용자가 선택한 검색엔진:
        {req.searchEngine}

        검색엔진 성향:
        {style_hint}

        중요 규칙:
        - 여행 대상이 독도처럼 좁은 범위이면 반드시 독도 범위 안에서만 추천
        - 다른 도시나 다른 광역 지역으로 확장 금지
        - 추천 장소 수가 부족하면 같은 지역 안의 세부 포인트, 감상 포인트, 이동 방식, 시간대 팁 중심으로 구성

        위 정보를 바탕으로 여행지를 추천하라.
        """
        result = run_chain(user_prompt)
        result["_meta"] = {
            "country": req.country,
            "searchEngine": req.searchEngine,
            "styleHint": style_hint,
        }
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/theme")
async def theme_search(req: ThemeSearchRequest):
    try:
        style_hint = ""
        if req.searchEngine:
            style_hint = get_search_engine_style(req.searchEngine)

        user_prompt = f"""
        테마:
        {req.theme}

        여행 대상:
        {req.country if req.country else "미지정"}

        사용자가 선택한 검색엔진:
        {req.searchEngine if req.searchEngine else "미지정"}

        검색엔진 성향:
        {style_hint if style_hint else "기본 추천"}

        중요 규칙:
        - 입력된 여행 대상 범위를 절대 벗어나지 말 것
        - 대상이 좁은 지역이면 그 안의 세부 스팟과 활동 중심으로 추천할 것
        - 다른 도시로 임의 확장 금지

        테마와 조건에 맞는 여행지를 추천하라.
        """
        return run_chain(user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommend")
async def recommend():
    try:
        user_prompt = "대중적으로 만족도가 높은 여행지 5개 추천."
        return run_chain(user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plan/daily")
async def daily_plan(req: DailyPlanRequest):
    try:
        user_prompt = f"""
        여행 도시: {req.location}

        여행 시간:
        시작 {req.start_time}
        종료 {req.end_time}

        이 시간 안에 가능한 하루 여행 일정을 만들어라.
        """
        return run_daily_plan_chain(user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course/location")
async def create_course(req: CourseRequest):
    try:
        user_prompt = f"""
        현재 위치 또는 시작 여행지: {req.location}

        위 위치를 기준으로 일반적인 관광 동선에 맞는 자연스러운 여행 코스를 만들어라.
        첫 장소는 가능하면 현재 위치 또는 가장 대표적인 장소로 구성하라.
        """
        return run_course_chain(user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course/customize/member/{member_id}")
async def customize_course(member_id: int, req: CustomizeCourseRequest):
    try:
        if not req.savedPlaces:
            raise HTTPException(status_code=400, detail="savedPlaces는 최소 1개 이상 필요합니다.")

        travel_context_text = ""
        if req.travelContext:
            travel_context_text = f"""
            여행 컨텍스트:
            moods={req.travelContext.moods}
            peopleCounts={req.travelContext.peopleCounts}
            avgWeathers={req.travelContext.avgWeathers}
            budgetMin={req.travelContext.budgetMin}
            budgetMax={req.travelContext.budgetMax}
            """

        user_prompt = f"""
        사용자 ID: {member_id}

        해당 사용자가 기존에 저장한 여행 코스:
        {req.savedPlaces}

        선택한 여행 스타일:
        {req.style}

        {travel_context_text}

        위 사용자의 저장 데이터를 바탕으로 스타일에 맞는 개인별 맞춤 코스를 재구성하라.
        """
        return run_customize_course_chain(user_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}