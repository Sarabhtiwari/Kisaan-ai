from fastapi import APIRouter
from app.db.expense_service import (
    get_farm_expenses,
    get_farm_summary,
    get_all_farms
)

router = APIRouter()

@router.get("/khata/farms")
async def get_farms(session_id: str):
    farms = get_all_farms(session_id)
    return {"farms": farms}

@router.get("/khata/expenses")
async def get_expenses(session_id: str, farm_name: str):
    expenses = get_farm_expenses(session_id, farm_name)
    return {"expenses": expenses}

@router.get("/khata/summary")
async def get_summary(session_id: str, farm_name: str):
    summary = get_farm_summary(session_id, farm_name)
    return summary