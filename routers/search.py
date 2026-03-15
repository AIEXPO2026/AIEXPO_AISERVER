from fastapi import APIRouter, HTTPException

from schemas.search import (
    SuperSearchRequest,
    ThemeSearchRequest,
)
from services.search_service import (
    super_search_service,
    theme_search_service,
    recommend_service,
)

router = APIRouter()


@router.post("/super")
async def super_search(req: SuperSearchRequest):
    try:
        return super_search_service(req.content, req.country, req.searchEngine)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/theme")
async def theme_search(req: ThemeSearchRequest):
    try:
        return theme_search_service(req.theme, req.country, req.searchEngine)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend")
async def recommend():
    try:
        return recommend_service()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))