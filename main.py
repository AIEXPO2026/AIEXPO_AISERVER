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

def run_chain(user_input: str):

    chain_input = {
        "user_input": user_input,
        "format_instructions": parser.get_format_instructions(),
    }

    chain = prompt_template | llm | parser

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


@app.get("/health")
def health():
    return {"status": "ok"}