from fastapi import APIRouter, HTTPException

from schemas.common import CourseRequest, CustomizeCourseRequest
from services.course_service import (
    create_course_by_location,
    customize_course_by_member,
)

router = APIRouter()


@router.post("/location")
async def create_course(req: CourseRequest):
    try:
        return create_course_by_location(req.location)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customize/member/{member_id}")
async def customize_course(member_id: int, req: CustomizeCourseRequest):
    try:
        return customize_course_by_member(
            member_id=member_id,
            style=req.style,
            saved_places=req.savedPlaces,
            travel_context=req.travelContext,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))