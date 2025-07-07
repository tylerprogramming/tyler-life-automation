from services import database as database_service

def get_dashboard_stats():
    return database_service.get_dashboard_stats()

def get_weekly_dashboard():
    return database_service.get_weekly_dashboard()