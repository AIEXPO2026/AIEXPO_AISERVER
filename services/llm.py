from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from core.config import OPENAI_API_KEY
from schemas.search import TravelResponse
from schemas.plan import DailyPlanResponse
from schemas.common import CourseResponse

llm = ChatOpenAI(
    model="gpt-5.4",
    temperature=0.3,
    api_key=OPENAI_API_KEY,
)

travel_parser = JsonOutputParser(pydantic_object=TravelResponse)
daily_parser = JsonOutputParser(pydantic_object=DailyPlanResponse)
course_parser = JsonOutputParser(pydantic_object=CourseResponse)


def invoke_chain(prompt_template, parser, user_input: str):
    chain = prompt_template | llm | parser
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": parser.get_format_instructions(),
    })