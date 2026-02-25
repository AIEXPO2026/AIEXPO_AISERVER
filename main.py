import os
import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Put it in .env or environment variables.")

client = OpenAI(api_key=API_KEY)

app = FastAPI(title="Cambodia AI Server", version="0.3.0")


# =========
# DTO
# =========
class SuperSearchRequest(BaseModel):
    content: str = Field(..., min_length=1)


class ThemeSearchRequest(BaseModel):
    theme: str = Field(..., min_length=1)


SYSTEM_COMMON = (
    "너는 여행지 추천 AI다. 반드시 JSON 배열로만 응답해라. "
    "각 원소는 다음 키를 가진다:\n"
    "- title: string (여행지 이름)\n"
    "- content: string (2~4문장 추천 이유/팁)\n"
    "- location: string (국가/도시/지역)\n"
    "- sources: string[] (참고자료 링크 2~5개)\n\n"
    "sources는 광고/블로그보다 '공식/권위/대형 가이드/공공기관/지도/유네스코' 우선.\n"
    "응답에 JSON 외의 텍스트를 절대 포함하지 마라."
)

SYSTEM_SUPER = SYSTEM_COMMON + " 사용자의 요구를 충족하는 추천을 만들어라."
SYSTEM_THEME = SYSTEM_COMMON + " 주어진 테마에 맞는 추천을 만들어라."
SYSTEM_RECOMMEND = SYSTEM_COMMON + " 대중적으로 만족도가 높은 여행지 추천을 만들어라."


def _ask_json(system_prompt: str, user_prompt: str, max_items: int = 5) -> List[dict]:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "user", "content": f"추천은 {max_items}개 이내."},
            {"role": "user", "content": "응답은 JSON 배열만. 다른 텍스트 금지."},
        ],
    )

    text = resp.choices[0].message.content.strip()

    # ```json ... ``` 제거
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

    try:
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("Not a JSON array")

        cleaned = []
        for item in data[:max_items]:
            if not isinstance(item, dict):
                continue
            sources = item.get("sources", [])
            if not isinstance(sources, list):
                sources = []
            sources = [str(s).strip() for s in sources[:5] if str(s).strip()]

            cleaned.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "content": str(item.get("content", "")).strip(),
                    "location": str(item.get("location", "")).strip(),
                    "sources": sources,
                }
            )
        return cleaned
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI response is not valid JSON: {e}. raw={text[:400]}..."
        )


@app.post("/search/super")
def super_search(req: SuperSearchRequest):
    prompt = (
        "사용자 요청:\n"
        f"{req.content}\n\n"
        "요청에 맞게 여행지를 추천하고, 각 추천마다 관련 참고자료 링크(sources) 2~5개를 포함해라."
    )
    return _ask_json(SYSTEM_SUPER, prompt, max_items=5)


@app.post("/search/theme")
def theme_search(req: ThemeSearchRequest):
    prompt = (
        f"테마: {req.theme}\n\n"
        "테마에 맞게 여행지를 추천하고, 각 추천마다 관련 참고자료 링크(sources) 2~5개를 포함해라."
    )
    return _ask_json(SYSTEM_THEME, prompt, max_items=5)


@app.get("/recommend")
def recommend():
    prompt = (
        "대중적으로 만족도가 높은 여행지 5개 추천. "
        "각 추천마다 관련 참고자료 링크(sources) 2~5개 포함."
    )
    return _ask_json(SYSTEM_RECOMMEND, prompt, max_items=5)


@app.get("/health")
def health():
    return {"status": "ok"}