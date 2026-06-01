# khata_tool.py
# AI-powered farm ledger tool
# Extracts expense data from natural language
# Performs DB operations based on farmer's request

from app.agent.state import AgentState
from app.config import GROQ_API_KEY
from app.db.expense_service import (
    save_expense,
    get_farm_expenses,
    get_farm_summary,
    compare_farms,
    get_time_expenses,
    get_category_total,
    get_all_farms
)
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import date, timedelta
from pydantic import BaseModel
from typing import Optional, List
import json

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# --- Pydantic model for structured extraction ---
# This defines exactly what fields Groq must return
class KhataExtraction(BaseModel):
    action: str
    # Possible values:
    # "add_expense"    → save new entry
    # "get_summary"    → show farm total
    # "compare"        → compare two khets
    # "time_report"    → expenses in time range
    # "category_total" → total for one category
    # "all_farms"      → show all khets
    # "incomplete"     → missing required fields

    farm_name: Optional[str] = None
    farm_names: Optional[List[str]] = None  # for compare
    amount: Optional[float] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    is_income: Optional[bool] = False
    crop: Optional[str] = None
    season: Optional[str] = "2024-25"
    expense_date: Optional[str] = None
    time_period: Optional[str] = None  # "this_month", "last_week" etc
    missing_fields: Optional[List[str]] = None
    follow_up_question: Optional[str] = None

# --- Extraction prompt ---
# We give Groq today's date and clear instructions
# Groq must return ONLY valid JSON matching KhataExtraction

EXTRACTION_PROMPT = """You are a farm expense tracker for Indian farmers.
Your job is to extract structured data from Hindi/English messages.

Today: {today}
Yesterday: {yesterday}
Current month: {current_month}

ENTITY EXTRACTION RULES:
1. Amount → any number in message = rupees (2500, 20000, 1500 etc)
2. Farm name → any "khet 1", "khet 2", "pehla khet", farm name mentioned
3. Income detection → if message has: becha, mila, aaya, bikri, sell, sold, karj liya = is_income true
4. Expense detection → lagaya, diya, kharcha, kharch = is_income false

CATEGORY MAPPING (map farmer's words to these):
- paani → paani, pani, irrigation, pump, sinchai, drip
- khad → khad, urea, DAP, fertilizer, NPK, potash
- beej → beej, seed, paudha, seedling
- dawai → dawai, spray, pesticide, keetnashak, fungicide
- majdoor → majdoor, mazdoor, labour, worker, kaarigar
- equipment → tractor, machine, pump set, thresher, kiraya
- bikri → becha, sell, sold, fasal bachi, amdani aayi
- karj → karj liya, loan liya, udhar liya
- karj_wapsi → karj diya, loan wapas, udhar chukaya
- anya → anything else

ACTION RULES:
- add_expense → farmer recording money spent OR earned
- get_summary → hisab, total, kitna kharcha, profit, loss, batao, dikhao
- compare → compare, tulna, dono, sabse zyada
- time_report → is mahine, pichle hafte, January mein, season mein
- category_total → paani pe kitna, khad ka total, majdoori kitni
- all_farms → sabke khet, har khet, sabka hisab
- incomplete → farm_name OR amount missing for add_expense

STRICT RULE FOR add_expense:
farm_name AND amount BOTH must be present in current message.
If either is missing → action = incomplete
Write follow_up_question in simple Hindi.

DATE RULES:
- aaj, today, nothing mentioned → {today}
- kal, yesterday → {yesterday}
- is mahine → time_period: this_month
- pichle hafte → time_period: last_week
- pichhle mahine → time_period: last_month
- is season → time_period: this_season

Farmer message: {message}

Return ONLY this JSON, no explanation, no markdown:
{{
    "action": "",
    "farm_name": null,
    "farm_names": null,
    "amount": null,
    "purpose": null,
    "category": null,
    "is_income": false,
    "crop": null,
    "season": "2024-25",
    "expense_date": null,
    "time_period": null,
    "missing_fields": null,
    "follow_up_question": null
}}"""


def extract_khata_info(message: str) -> KhataExtraction:
    """
    Ask Groq to extract structured expense info
    from farmer's natural language message.
    Returns KhataExtraction object.
    """
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    current_month = date.today().strftime("%B %Y")

    prompt = EXTRACTION_PROMPT.format(
        today=today,
        yesterday=yesterday,
        current_month=current_month,
        message=message
    )

    response = llm.invoke([
        SystemMessage(content="You are a JSON extraction assistant. Return only valid JSON."),
        HumanMessage(content=prompt)
    ])

    # Clean response — remove markdown if Groq adds it
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    # Parse JSON into Pydantic model
    try:
        data = json.loads(content)
        return KhataExtraction(**data)
    except Exception as e:
        print(f"Extraction error: {e}")
        # Return incomplete if parsing fails
        return KhataExtraction(
            action="incomplete",
            missing_fields=["all"],
            follow_up_question="Maaf karein, samajh nahi aaya. Kripaya dobara likhein jaise: 'khet 2 mein 2500 ka paani lagaya'"
        )
    

def get_date_range(time_period: str) -> tuple:
    """
    Convert time period string to start and end dates.
    Returns (start_date, end_date) as strings.
    """
    today = date.today()

    if time_period == "this_month":
        start = today.replace(day=1)
        end = today
    elif time_period == "last_week":
        start = today - timedelta(days=7)
        end = today
    elif time_period == "last_month":
        # First day of last month
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start = last_month_end.replace(day=1)
        end = last_month_end
    elif time_period == "this_season":
        start = date(2024, 10, 1)
        end = today
    else:
        # Default to last 30 days
        start = today - timedelta(days=30)
        end = today

    return start.isoformat(), end.isoformat()


def format_expense_list(expenses: list) -> str:
    """
    Convert list of expense dicts to readable text
    for synthesizer to format into Hindi.
    """
    if not expenses:
        return "Koi kharcha nahi mila."

    lines = []
    total_expense = 0
    total_income = 0

    for exp in expenses:
        amount = float(exp["amount"])
        date_str = exp["expense_date"]
        category = exp["category"]
        purpose = exp["purpose"]
        is_income = exp.get("is_income", False)

        if is_income:
            total_income += amount
            lines.append(f"{date_str} | {category} | +{amount} (income) | {purpose}")
        else:
            total_expense += amount
            lines.append(f"{date_str} | {category} | -{amount} | {purpose}")

    lines.append(f"\nTotal Kharcha: {total_expense}")
    lines.append(f"Total Amdani: {total_income}")
    lines.append(f"Net Profit/Loss: {total_income - total_expense}")

    return "\n".join(lines)


def khata_node(state: AgentState) -> AgentState:
    session_id = state["session_id"]
    message = state["message"]

    # Step 1 — Extract structured info
    extracted = extract_khata_info(message)

    # print(f"DEBUG extracted action: {extracted.action}")
    # print(f"DEBUG extracted farm_name: {extracted.farm_name}")

    # Step 2 — Python level fixes
    # If get_summary but no farm_name → show all farms
    if extracted.action == "get_summary" and not extracted.farm_name:
        extracted.action = "all_farms"

    # If compare but only one farm → get_summary instead
    if extracted.action == "compare" and not extracted.farm_names:
        if extracted.farm_name:
            extracted.action = "get_summary"
        else:
            extracted.action = "all_farms"

    # Step 3 — Handle incomplete info
    if extracted.action == "add_expense":
        missing = []
        if not extracted.farm_name:
            missing.append("khet ka naam")
        if not extracted.amount:
            missing.append("kitne rupaye")
        if not extracted.category:
            missing.append("kharche ka karan")

        if missing:
            missing_text = " aur ".join(missing)
            state["tool_result"] = f"Kripaya batayen: {missing_text}?"
            state["tool_results"] = [state["tool_result"]]
            return state

    if extracted.action == "incomplete" or extracted.missing_fields:
        state["tool_result"] = extracted.follow_up_question or "Kripaya khet ka naam, amount aur kharche ka karan batayen."
        state["tool_results"] = [state["tool_result"]]
        return state

    # Step 4 — Route to correct operation
    result_text = ""

    if extracted.action == "add_expense":
        saved = save_expense(
            session_id=session_id,
            farm_name=extracted.farm_name,
            category=extracted.category,
            purpose=extracted.purpose or extracted.category,
            amount=extracted.amount,
            is_income=extracted.is_income or False,
            crop=extracted.crop,
            season=extracted.season or "2024-25",
            expense_date=extracted.expense_date,
        )
        if saved:
            entry_type = "amdani" if extracted.is_income else "kharcha"
            result_text = (
                f"Saved: Farm={extracted.farm_name}, "
                f"Amount={extracted.amount}, "
                f"Category={extracted.category}, "
                f"Type={entry_type}, "
                f"Date={extracted.expense_date}"
            )
        else:
            result_text = "Error saving. Please try again."

    elif extracted.action == "get_summary":
        summary = get_farm_summary(session_id, extracted.farm_name, extracted.season)
        result_text = (
            f"Farm: {extracted.farm_name}\n"
            f"Total Kharcha: {summary.get('total_expense', 0)}\n"
            f"Total Amdani: {summary.get('total_income', 0)}\n"
            f"Net Profit: {summary.get('net_profit', 0)}\n"
            f"Category Breakdown: {summary.get('category_breakdown', {})}\n"
            f"Total Entries: {summary.get('expense_count', 0)}"
        )

    elif extracted.action == "compare":
        farm_names = extracted.farm_names or []
        if extracted.farm_name and extracted.farm_name not in farm_names:
            farm_names.append(extracted.farm_name)
        if not farm_names:
            farm_names = get_all_farms(session_id)
        results = compare_farms(session_id, farm_names, extracted.season)
        lines = ["Comparison:"]
        for r in results:
            lines.append(
                f"{r['farm_name']}: "
                f"Kharcha={r.get('total_expense', 0)}, "
                f"Amdani={r.get('total_income', 0)}, "
                f"Profit={r.get('net_profit', 0)}"
            )
        result_text = "\n".join(lines)

    elif extracted.action == "time_report":
        start, end = get_date_range(extracted.time_period or "this_month")
        expenses = get_time_expenses(
            session_id, start, end, extracted.farm_name
        )
        result_text = f"Time period: {start} to {end}\n"
        result_text += format_expense_list(expenses)

    elif extracted.action == "category_total":
        result = get_category_total(
            session_id,
            extracted.category,
            extracted.farm_name,
            extracted.season
        )
        result_text = (
            f"Category: {extracted.category}\n"
            f"Total: {result.get('total', 0)}\n"
            f"Entries: {result.get('count', 0)}"
        )

    elif extracted.action == "all_farms":
        farms = get_all_farms(session_id)
        # print(f"DEBUG all farms found: {farms}")
        if not farms:
            result_text = "Koi khet nahi mila. Pehle kuch kharcha darj karein."
        else:
            lines = ["All farms summary:"]
            for farm in farms:
                summary = get_farm_summary(session_id, farm)
                lines.append(
                    f"{farm}: "
                    f"Kharcha={summary.get('total_expense', 0)}, "
                    f"Amdani={summary.get('total_income', 0)}, "
                    f"Profit={summary.get('net_profit', 0)}"
                )
            result_text = "\n".join(lines)

    else:
        result_text = "Samajh nahi aaya. Dobara likhein jaise: 'khet 1 ka hisab batao'"

    state["tool_result"] = result_text
    state["tool_results"] = [result_text]
    return state