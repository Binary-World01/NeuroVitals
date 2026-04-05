"""
Community Router - Community health intelligence
"""
from fastapi import APIRouter, HTTPException
from app.schemas import CommunityHealthData
from app.services.community_service import community_service

router = APIRouter(prefix="/community", tags=["Community"])


@router.get("/heatmap", response_model=CommunityHealthData)
async def get_community_heatmap():
    """Get community health intelligence heatmap data"""
    try:
        result = community_service.get_heatmap_data()
        return CommunityHealthData(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heatmap failed: {str(e)}")
