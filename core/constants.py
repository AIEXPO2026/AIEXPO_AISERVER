from typing import Dict, List

COUNTRY_SEARCH_ENGINES: Dict[str, List[Dict[str, str]]] = {
    "대한민국": [
        {"code": "naver", "label": "네이버"},
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "일본": [
        {"code": "google", "label": "구글"},
        {"code": "yahoo", "label": "야후 재팬"},
        {"code": "bing", "label": "빙"},
    ],
    "미국": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
        {"code": "duckduckgo", "label": "덕덕고"},
    ],
    "대만": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "태국": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
    "프랑스": [
        {"code": "google", "label": "구글"},
        {"code": "bing", "label": "빙"},
    ],
}

DEFAULT_ENGINES = [
    {"code": "google", "label": "구글"},
    {"code": "bing", "label": "빙"},
]

SEARCH_ENGINE_STYLE = {
    "naver": "로컬 인기 스팟과 맛집 중심",
    "google": "대표 관광지와 랜드마크 중심",
    "bing": "감성적인 명소와 사진 스팟 중심",
    "yahoo": "대중적인 관광지와 지역 명소 중심",
    "duckduckgo": "균형 잡힌 탐색형 추천",
}