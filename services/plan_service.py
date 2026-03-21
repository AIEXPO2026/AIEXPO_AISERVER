from prompts.daily_prompts import daily_prompt_template
from services.llm import invoke_chain, daily_parser
from services.cache_service import (
    normalize_text,
    make_hash_key,
    get_json_cache,
    set_json_cache,
)


def create_daily_plan(location: str, start_time: str, end_time: str):
    payload = {
        "location": normalize_text(location),
        "start_time": start_time.strip(),
        "end_time": end_time.strip(),
    }
    key = f"travel:plan:daily:v1:{make_hash_key(payload)}"

    cached = get_json_cache(key)
    if cached is not None:
        return cached

    user_prompt = f"""
    여행 도시: {location}

    여행 시간:
    시작 {start_time}
    종료 {end_time}

    이 시간 안에 가능한 하루 여행 일정을 만들어라.
    """

    result = invoke_chain(daily_prompt_template, daily_parser, user_prompt)
    set_json_cache(key, result, ttl=600)
    return result