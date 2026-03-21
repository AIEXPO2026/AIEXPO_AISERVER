from fastapi import HTTPException

from prompts.course_prompts import (
    course_prompt_template,
    customize_prompt_template,
)
from services.llm import invoke_chain, course_parser
from schemas.common import TravelContextRequest
from services.cache_service import (
    normalize_text,
    make_hash_key,
    get_json_cache,
    set_json_cache,
    register_group_key,
)


def create_course_by_location(location: str):
    payload = {
        "location": normalize_text(location),
    }
    key = f"travel:course:location:v1:{make_hash_key(payload)}"

    cached = get_json_cache(key)
    if cached is not None:
        return cached

    user_prompt = f"""
    현재 위치 또는 시작 여행지: {location}

    위 위치를 기준으로 일반적인 관광 동선에 맞는 자연스러운 여행 코스를 만들어라.
    첫 장소는 가능하면 현재 위치 또는 가장 대표적인 장소로 구성하라.
    """

    result = invoke_chain(course_prompt_template, course_parser, user_prompt)
    set_json_cache(key, result, ttl=1800)
    return result


def save_course_by_location(nickname: str, location: str):
    result = create_course_by_location(location)
    result["nickname"] = nickname
    result["location"] = location
    return result


def customize_course_by_member(
    member_id: int,
    style: str,
    saved_places: list[str],
    travel_context: TravelContextRequest | None = None,
):
    travel_context_dict = travel_context.model_dump() if travel_context else None

    payload = {
        "member_id": member_id,
        "style": normalize_text(style),
        "saved_places": [p.strip() for p in saved_places] if saved_places else [],
        "travel_context": travel_context_dict,
    }
    key = f"travel:course:custom:v1:{make_hash_key(payload)}"

    cached = get_json_cache(key)
    if cached is not None:
        return cached

    travel_context_text = ""
    if travel_context:
        travel_context_text = f"""
        여행 컨텍스트:
        moods={travel_context.moods}
        peopleCounts={travel_context.peopleCounts}
        avgWeathers={travel_context.avgWeathers}
        budgetMin={travel_context.budgetMin}
        budgetMax={travel_context.budgetMax}
        """

    user_prompt = f"""
    사용자 ID: {member_id}

    해당 사용자가 기존에 저장한 여행 코스:
    {saved_places if saved_places else "없음"}

    선택한 여행 스타일:
    {style}

    {travel_context_text}

    위 사용자의 저장 데이터를 바탕으로 스타일에 맞는 개인별 맞춤 코스를 재구성하라.
    """

    result = invoke_chain(customize_prompt_template, course_parser, user_prompt)
    set_json_cache(key, result, ttl=600)

    register_group_key(
        group_key=f"travel:cachekeys:member:{member_id}",
        cache_key=key,
        ttl=600,
    )

    return result