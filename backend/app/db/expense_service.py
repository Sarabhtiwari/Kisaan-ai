from app.db.supabase import client
from typing import List, Optional
from datetime import date, datetime

def save_expense(
    session_id: str,
    farm_name: str,
    category: str,
    purpose: str,
    amount: float,
    is_income: bool = False,
    crop: str = None,
    season: str = "2026-27",
    expense_date: str = None,
    notes: str = None
) -> dict:
    """
    Save one expense or income entry to database.
    
    amount positive = expense (money going OUT)
    amount negative = income (money coming IN)
    is_income = True means farmer received money
    """
    try:
        # If no date provided, use today
        if not expense_date:
            expense_date = date.today().isoformat()

        response = client.table("expenses").insert({
            "session_id":   session_id,
            "farm_name":    farm_name.lower().strip(),
            "category":     category,
            "purpose":      purpose,
            "amount":       amount,
            "is_income":    is_income,
            "crop":         crop,
            "season":       season,
            "expense_date": expense_date,
            "notes":        notes
        }).execute()

        return response.data[0] if response.data else {}

    except Exception as e:
        print(f"Error saving expense: {e}")
        return {}
    
def get_farm_expenses(
    session_id: str,
    farm_name: str,
    season: str = None,
    limit: int = 50
) -> List[dict]:
    """
    Get all expenses for one specific khet.
    Returns list of expenses ordered by date.
    """
    try:
        query = client.table("expenses")\
            .select("*")\
            .eq("session_id", session_id)\
            .eq("farm_name", farm_name.lower().strip())\
            .order("expense_date", desc=True)\
            .limit(limit)

        # Filter by season if provided
        if season:
            query = query.eq("season", season)

        response = query.execute()
        return response.data or []

    except Exception as e:
        print(f"Error getting farm expenses: {e}")
        return []


def get_farm_summary(
    session_id: str,
    farm_name: str,
    season: str = None
) -> dict:
    """
    Get total expense, total income, and net profit
    for one khet.
    
    Returns:
    {
        "total_expense": 15000,
        "total_income": 25000,
        "net_profit": 10000,
        "category_breakdown": {...}
    }
    """
    try:
        expenses = get_farm_expenses(session_id, farm_name, season)

        total_expense = 0
        total_income = 0
        category_breakdown = {}

        for exp in expenses:
            amount = float(exp["amount"])
            category = exp["category"]

            if exp["is_income"]:
                total_income += amount
            else:
                total_expense += amount

            # Category wise breakdown
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += amount

        return {
            "total_expense":      total_expense,
            "total_income":       total_income,
            "net_profit":         total_income - total_expense,
            "category_breakdown": category_breakdown,
            "expense_count":      len(expenses)
        }

    except Exception as e:
        print(f"Error getting summary: {e}")
        return {}

def compare_farms(
    session_id: str,
    farm_names: List[str],
    season: str = None
) -> List[dict]:
    """
    Compare multiple khets side by side.
    Returns summary for each khet.
    
    Example:
    compare_farms("farmer_abc", ["khet 1", "khet 2"])
    Returns:
    [
        {"farm": "khet 1", "total_expense": 15000, "net_profit": 10000},
        {"farm": "khet 2", "total_expense": 8000,  "net_profit": 5000}
    ]
    """
    try:
        results = []
        for farm_name in farm_names:
            summary = get_farm_summary(session_id, farm_name, season)
            summary["farm_name"] = farm_name
            results.append(summary)
        return results

    except Exception as e:
        print(f"Error comparing farms: {e}")
        return []


def get_time_expenses(
    session_id: str,
    start_date: str,
    end_date: str,
    farm_name: str = None
) -> List[dict]:
    """
    Get expenses between two dates.
    Optionally filter by farm.
    
    Used for:
    - "is mahine ka kharcha"
    - "January mein kya kya hua"
    - "pichle hafte ka total"
    """
    try:
        query = client.table("expenses")\
            .select("*")\
            .eq("session_id", session_id)\
            .gte("expense_date", start_date)\
            .lte("expense_date", end_date)\
            .order("expense_date", desc=True)

        if farm_name:
            query = query.eq("farm_name", farm_name.lower().strip())

        response = query.execute()
        return response.data or []

    except Exception as e:
        print(f"Error getting time expenses: {e}")
        return []


# Category aliases — maps all variations to one canonical name
CATEGORY_ALIASES = {
    "paani":      ["paani", "pani", "irrigation", "water", "sinchai"],
    "khad":       ["khad", "fertilizer", "urea", "dap", "npk", "potash"],
    "beej":       ["beej", "seed", "seeds", "seedling", "paudha"],
    "dawai":      ["dawai", "pesticide", "spray", "insecticide", "fungicide", "keetnashak"],
    "majdoor":    ["majdoor", "mazdoor", "labour", "labor", "worker", "kaarigar"],
    "equipment":  ["equipment", "tractor", "machine", "pump", "thresher", "kiraya"],
    "bikri":      ["bikri", "sell", "sold", "sale", "amdani"],
    "karj":       ["karj", "loan", "udhar"],
    "karj_wapsi": ["karj_wapsi", "repaid", "wapas"],
    "anya":       ["anya", "other", "misc"]
}

def get_category_variants(category: str) -> list:
    """Get all possible DB values for a category name."""
    category_lower = category.lower()
    
    # Check if it matches any canonical name or alias
    for canonical, aliases in CATEGORY_ALIASES.items():
        if category_lower == canonical or category_lower in aliases:
            return aliases  # return all variants to search
    
    # If not found, just search for the exact value
    return [category_lower]


def get_category_total(
    session_id: str,
    category: str,
    farm_name: str = None,
    season: str = None
) -> dict:
    """
    Get total spent on one category.
    Searches all variants of category name.
    """
    try:
        # Get all possible values for this category
        variants = get_category_variants(category)
        
        all_expenses = []
        
        # Search for each variant
        for variant in variants:
            query = client.table("expenses")\
                .select("*")\
                .eq("session_id", session_id)\
                .eq("category", variant)

            if farm_name:
                query = query.eq("farm_name", farm_name.lower().strip())
            if season:
                query = query.eq("season", season)

            response = query.execute()
            if response.data:
                all_expenses.extend(response.data)

        # Remove duplicates by id
        seen = set()
        unique_expenses = []
        for exp in all_expenses:
            if exp["id"] not in seen:
                seen.add(exp["id"])
                unique_expenses.append(exp)

        total = sum(float(e["amount"]) for e in unique_expenses)

        return {
            "category": category,
            "total":    total,
            "count":    len(unique_expenses),
            "entries":  unique_expenses
        }

    except Exception as e:
        print(f"Error getting category total: {e}")
        return {}

def get_all_farms(session_id: str) -> List[str]:
    """
    Get list of all khet names for this farmer.
    Used when farmer asks "sabke kheton ka hisab"
    """
    try:
        response = client.table("expenses")\
            .select("farm_name")\
            .eq("session_id", session_id)\
            .execute()

        if not response.data:
            return []

        # Get unique farm names
        farms = list(set(
            exp["farm_name"] for exp in response.data
        ))
        return sorted(farms)

    except Exception as e:
        print(f"Error getting farms: {e}")
        return []

