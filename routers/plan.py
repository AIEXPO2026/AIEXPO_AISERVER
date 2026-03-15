from fastapi import APIRouter, HTTPException

from schemas.plan import DailyPlanRequest
from services.plan_service import create_daily_plan

router = APIRouter()


@router.post("/daily")
async def daily_plan(req: DailyPlanRequest):
    try:
        return create_daily_plan(req.location, req.start_time, req.end_time)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))