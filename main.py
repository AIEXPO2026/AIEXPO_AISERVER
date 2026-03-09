import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="Cambodia AI Server", version="1.0.0")

class SuperSearchRequest(BaseModel):
    content: str = Field(..., min_length=1)

class ThemeSearchRequest(BaseModel):
    theme: str = Field(..., min_length=1)

class TravelItem(BaseModel):
    title: str = Field(description="여행지 이름")
    content: str = Field(description="2~4문장 추천 이유/팁")
    location: str = Field(description="국가/도시/지역")
    sources: List[str] = Field(description="참고자료 링크 2~5개")

class TravelResponse(BaseModel):
    results: List[TravelItem]

class DailyPlanRequest(BaseModel):
    location: str = Field(..., description="여행 도시 또는 지역")
    start_time: str = Field(..., description="여행 시작 시간 예: 10:00")
    end_time: str = Field(..., description="여행 종료 시간 예: 18:00")


class PlanItem(BaseModel):
    time: str = Field(description="시간")
    activity: str = Field(description="활동 내용")


class DailyPlanResponse(BaseModel):
    plan: List[PlanItem]


daily_parser = JsonOutputParser(pydantic_object=DailyPlanResponse)

parser = JsonOutputParser(pydantic_object=TravelResponse)

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

            규칙
            - 시간 순서로 정렬
            - 장소 이동을 고려한 자연스러운 일정
            - 너무 촘촘하지 않게 구성
            - 점심 식사 포함

            반드시 JSON 형식으로 응답

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

@app.get("/health")
def health():
    return {"status": "ok"}