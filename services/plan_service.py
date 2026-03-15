from prompts.daily_prompts import daily_prompt_template
from services.llm import invoke_chain, daily_parser


def create_daily_plan(location: str, start_time: str, end_time: str):
    user_prompt = f"""
    여행 도시: {location}

    여행 시간:
    시작 {start_time}
    종료 {end_time}

    이 시간 안에 가능한 하루 여행 일정을 만들어라.
    """
    return invoke_chain(daily_prompt_template, daily_parser, user_prompt)