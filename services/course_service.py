from fastapi import HTTPException

from prompts.course_prompts import (
    course_prompt_template,
    customize_prompt_template,
)
from services.llm import invoke_chain, course_parser
from schemas.common import TravelContextRequest


def create_course_by_location(location: str):
    user_prompt = f"""
    현재 위치 또는 시작 여행지: {location}

    위 위치를 기준으로 일반적인 관광 동선에 맞는 자연스러운 여행 코스를 만들어라.
    첫 장소는 가능하면 현재 위치 또는 가장 대표적인 장소로 구성하라.
    """
    return invoke_chain(course_prompt_template, course_parser, user_prompt)


def customize_course_by_member(
    member_id: int,
    style: str,
    saved_places: list[str],
    travel_context: TravelContextRequest | None = None,
):
    if not saved_places:
        raise HTTPException(status_code=400, detail="savedPlaces는 최소 1개 이상 필요합니다.")

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
    {saved_places}

    선택한 여행 스타일:
    {style}

    {travel_context_text}

    위 사용자의 저장 데이터를 바탕으로 스타일에 맞는 개인별 맞춤 코스를 재구성하라.
    """

    return invoke_chain(customize_prompt_template, course_parser, user_prompt)