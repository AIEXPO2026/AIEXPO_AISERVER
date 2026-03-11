import os
from typing import List
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from typing import List, Optional
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime, Date, Integer, ForeignKey, Time, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime, date

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Cambodia AI Server", version="1.1.0")


class Travel(Base):
    __tablename__ = "travel"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    avg_weather = Column(String(255), nullable=True)
    budget_max = Column(Integer, nullable=True)
    budget_min = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    end_date = Column(Date, nullable=True)
    mood = Column(Integer, nullable=False, default=0)
    people_count = Column(Integer, nullable=True)
    public_travel = Column(Integer, nullable=False, default=0)
    start_date = Column(Date, nullable=True)
    travel_status = Column(String(50), nullable=True)
    member_id = Column(BigInteger, nullable=True)


class Attraction(Base):
    __tablename__ = "attractions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=True)
    detail = Column(String(255), nullable=True)
    duration = Column(Time, nullable=True)
    photourl = Column(String(255), nullable=True)
    travel_id = Column(BigInteger, ForeignKey("travel.id"), nullable=True)


class SuperSearchRequest(BaseModel):
    content: str = Field(..., min_length=1)

class ThemeSearchRequest(BaseModel):
    theme: str = Field(..., min_length=1)


class CourseRequest(BaseModel):
    location: str = Field(..., description="현재 위치 또는 시작 여행지 예: 후쿠오카 타워")


class SaveCourseRequest(BaseModel):
    member_id: int = Field(..., description="회원 ID")
    location: str = Field(..., description="현재 위치 또는 시작 여행지 예: 후쿠오카 타워")


class CustomizeCourseRequest(BaseModel):
    style: str = Field(..., description="감성 / 힐링 / 혼행 / 액티비티 / 맛집")


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


class SavedCourseResponse(BaseModel):
    travel_id: int
    location: str
    course: List[CourseItem]


parser = JsonOutputParser(pydantic_object=TravelResponse)
daily_parser = JsonOutputParser(pydantic_object=DailyPlanResponse)
course_parser = JsonOutputParser(pydantic_object=CourseResponse)

llm = ChatOpenAI(
    model="gpt-4o-mini",
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

            {format_instructions}
            """,
        ),
        (
            "user",
            "{user_input}",
        ),
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
        (
            "user",
            "{user_input}",
        ),
    ]
)

course_prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            너는 위치 기반 여행 코스 생성 AI다.
            사용자가 입력한 현재 위치 또는 시작 여행지를 기준으로,
            주변 관광지 후보를 참고해서 자연스러운 여행 코스를 만들어라.

            규칙:
            - 방문 순서는 1부터 시작
            - 현재 위치와 가까운 장소부터 자연스럽게 이어지도록 구성
            - 중복 장소 금지
            - course는 최대 4개로 구성
            - 반드시 JSON 형식으로 응답

            {format_instructions}
            """,
        ),
        (
            "user",
            "{user_input}",
        ),
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
        (
            "user",
            "{user_input}",
        ),
    ]
)

def run_chain(user_input: str):
    chain_input = {
        "user_input": user_input,
        "format_instructions": parser.get_format_instructions(),
    }
    chain = prompt_template | llm | parser
    return chain.invoke(chain_input)

def run_daily_plan_chain(user_input: str):
    chain_input = {
        "user_input": user_input,
        "format_instructions": daily_parser.get_format_instructions(),
    }
    chain = daily_prompt_template | llm | daily_parser
    return chain.invoke(chain_input)


def run_course_chain(user_input: str):
    chain_input = {
        "user_input": user_input,
        "format_instructions": course_parser.get_format_instructions(),
    }
    chain = course_prompt_template | llm | course_parser
    return chain.invoke(chain_input)


def run_customize_course_chain(user_input: str):
    chain_input = {
        "user_input": user_input,
        "format_instructions": course_parser.get_format_instructions(),
    }
    chain = customize_prompt_template | llm | course_parser
    return chain.invoke(chain_input)


def get_nearby_places(location: str) -> List[str]:
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_MAPS_API_KEY가 설정되지 않았습니다.")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"tourist attractions near {location}",
        "key": GOOGLE_MAPS_API_KEY,
        "language": "ko",
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    status = data.get("status")
    if status not in ["OK", "ZERO_RESULTS"]:
        raise HTTPException(
            status_code=500,
            detail=f"Google Places API 오류: {status}"
        )

    places = []
    for item in data.get("results", [])[:8]:
        name = item.get("name")
        if name and name not in places:
            places.append(name)

    return places


def save_course_to_db(member_id: int, course_items: List[dict]) -> int:
    db: Session = SessionLocal()

    try:
        travel = Travel(
            created_at=datetime.utcnow(),
            start_date=date.today(),
            end_date=date.today(),
            mood=0,
            people_count=1,
            public_travel=0,
            travel_status="TRAVEL_PLANNED",
            member_id=member_id,
            avg_weather=None,
            budget_min=None,
            budget_max=None,
        )

        db.add(travel)
        db.flush()

        for item in course_items:
            attraction = Attraction(
                created_at=datetime.utcnow(),
                detail=item["place"],
                duration=None,
                photourl=None,
                travel_id=travel.id,
            )
            db.add(attraction)

        db.commit()
        return travel.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_member_saved_course_from_db(member_id: int) -> List[str]:
    db: Session = SessionLocal()

    try:
        rows = (
            db.query(Attraction.detail)
            .join(Travel, Attraction.travel_id == Travel.id)
            .filter(Travel.member_id == member_id)
            .order_by(Travel.created_at.desc(), Attraction.id.asc())
            .all()
        )

        places = []
        for row in rows:
            detail = row[0]
            if detail and detail not in places:
                places.append(detail)

        return places[:8]

    finally:
        db.close()


@app.post("/search/super")
async def super_search(req: SuperSearchRequest):
    try:
        user_prompt = f"""
        사용자 요청:
        {req.content}
        요구에 맞는 여행지를 추천하라.
        """
        return run_chain(user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/theme")
async def theme_search(req: ThemeSearchRequest):
    try:
        user_prompt = f"""
        테마:
        {req.theme}
        테마에 맞는 여행지를 추천하라.
        """
        return run_chain(user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recommend")
async def recommend():
    try:
        user_prompt = """
        대중적으로 만족도가 높은 여행지 5개 추천.
        """
        return run_chain(user_prompt)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course/location")
async def create_course(req: CourseRequest):
    try:
        places = get_nearby_places(req.location)

        if not places:
            raise HTTPException(status_code=404, detail="주변 장소를 찾지 못했습니다.")

        user_prompt = f"""
        현재 위치: {req.location}

        주변 장소 후보:
        {places}

        위 장소들을 활용해서 자연스러운 여행 코스를 만들어라.
        첫 장소는 가능하면 현재 위치 또는 가장 대표적인 장소로 구성하라.
        """
        return run_course_chain(user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course/location/save")
async def create_and_save_course(req: SaveCourseRequest):
    try:
        places = get_nearby_places(req.location)

        if not places:
            raise HTTPException(status_code=404, detail="주변 장소를 찾지 못했습니다.")

        user_prompt = f"""
        현재 위치: {req.location}

        주변 장소 후보:
        {places}

        위 장소들을 활용해서 자연스러운 여행 코스를 만들어라.
        첫 장소는 가능하면 현재 위치 또는 가장 대표적인 장소로 구성하라.
        """
        course_result = run_course_chain(user_prompt)
        travel_id = save_course_to_db(req.member_id, course_result["course"])

        return {
            "travel_id": travel_id,
            "location": req.location,
            "course": course_result["course"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/course/customize/member/{member_id}")
async def customize_course(member_id: int, req: CustomizeCourseRequest):
    try:
        saved_places = get_member_saved_course_from_db(member_id)

        if not saved_places:
            raise HTTPException(status_code=404, detail="해당 사용자의 저장된 코스를 찾지 못했습니다.")

        user_prompt = f"""
        사용자 ID: {member_id}

        해당 사용자가 기존에 저장한 여행 코스:
        {saved_places}

        선택한 여행 스타일:
        {req.style}

        위 사용자의 저장 데이터를 바탕으로 스타일에 맞는 개인별 맞춤 코스를 재구성하라.
        """
        return run_customize_course_chain(user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}