from langchain_core.prompts import ChatPromptTemplate

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
        ("user", "{user_input}"),
    ]
)