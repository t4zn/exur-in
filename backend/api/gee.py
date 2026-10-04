from fastapi import APIRouter, Query
from typing import Optional
from backend.earth_engine import (
    get_gee_harmonization_data,
    get_gee_orbital_anchor_for_coordinate,
)

router = APIRouter()

@router.get("/gee")
async def get_gee(
    type: Optional[str] = Query(None),
    lat: Optional[float] = Query(28.6139),
    lng: Optional[float] = Query(77.2090),
):
    try:
        if type == "anchor":
            data = get_gee_orbital_anchor_for_coordinate(lat, lng)
            return {"success": True, "data": data}

        data = get_gee_harmonization_data()
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}
