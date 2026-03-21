from core.constants import SEARCH_ENGINE_STYLE
from prompts.search_prompts import search_prompt_template
from services.llm import invoke_chain, travel_parser
from services.cache_service import (
    normalize_text,
    make_hash_key,
    get_json_cache,
    set_json_cache,
)


def get_search_engine_style(search_engine: str) -> str:
    return SEARCH_ENGINE_STYLE.get(search_engine, "균형 잡힌 여행지 추천")


def super_search_service(content: str, country: str, search_engine: str):
    payload = {
        "content": normalize_text(content),
        "country": normalize_text(country),
        "search_engine": normalize_text(search_engine),
    }
    key = f"travel:super:v1:{make_hash_key(payload)}"

    cached = get_json_cache(key)
    if cached is not None:
        return cached

    style_hint = get_search_engine_style(search_engine)

    user_prompt = f"""
    사용자 요청:
    {content}

    여행 대상:
    {country}

    사용자가 선택한 검색엔진:
    {search_engine}

    검색엔진 성향:
    {style_hint}

    중요 규칙:
    - 여행 대상이 독도처럼 좁은 범위이면 반드시 독도 범위 안에서만 추천
    - 다른 도시나 다른 광역 지역으로 확장 금지
    - 추천 장소 수가 부족하면 같은 지역 안의 세부 포인트, 감상 포인트, 이동 방식, 시간대 팁 중심으로 구성

    위 정보를 바탕으로 여행지를 추천하라.
    """

    result = invoke_chain(search_prompt_template, travel_parser, user_prompt)
    result["_meta"] = {
        "country": country,
        "searchEngine": search_engine,
        "styleHint": style_hint,
    }

    set_json_cache(key, result, ttl=300)
    return result


def theme_search_service(theme: str, country: str | None, search_engine: str | None):
    payload = {
        "theme": normalize_text(theme),
        "country": normalize_text(country),
        "search_engine": normalize_text(search_engine),
    }
    key = f"travel:theme:v1:{make_hash_key(payload)}"

    cached = get_json_cache(key)
    if cached is not None:
        return cached

    style_hint = get_search_engine_style(search_engine) if search_engine else ""

    user_prompt = f"""
    테마:
    {theme}

    여행 대상:
    {country if country else "미지정"}

    사용자가 선택한 검색엔진:
    {search_engine if search_engine else "미지정"}

    검색엔진 성향:
    {style_hint if style_hint else "기본 추천"}

    중요 규칙:
    - 입력된 여행 대상 범위를 절대 벗어나지 말 것
    - 대상이 좁은 지역이면 그 안의 세부 스팟과 활동 중심으로 추천할 것
    - 다른 도시로 임의 확장 금지

    테마와 조건에 맞는 여행지를 추천하라.
    """

    result = invoke_chain(search_prompt_template, travel_parser, user_prompt)
    set_json_cache(key, result, ttl=900)
    return result


def recommend_service():
    return invoke_chain(
        search_prompt_template,
        travel_parser,
        "대중적으로 만족도가 높은 여행지 5개 추천."
    )