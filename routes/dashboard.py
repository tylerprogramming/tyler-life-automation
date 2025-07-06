from fastapi import APIRouter
from services import dashboard as dashboard_service

router = APIRouter()

@router.get("/stats")
def dashboard_stats():
    return dashboard_service.get_dashboard_stats()

@router.get("/weekly")
def dashboard_weekly():
    return dashboard_service.get_weekly_dashboard()