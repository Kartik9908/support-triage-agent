import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from app.schemas import TriageResult
from app.mcp_server import get_order_status

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class TicketState(TypedDict):
    customer_email: str
    message: str
    triage: Optional[dict]
    order_details: Optional[dict]
    human_approved: Optional[bool]
    final_status: str
    final_reply: str

def triage_and_lookup(state: TicketState):
    prompt = f"""
    Analyze this customer support email and return structured triage data.
    Customer Email: {state['customer_email']}
    Message: {state['message']}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": TriageResult,
        },
    )
    triage_data = TriageResult.model_validate_json(response.text).model_dump()

    order_details = None
    if triage_data.get("order_id"):
        order_details = get_order_status(triage_data["order_id"])

    return {"triage": triage_data, "order_details": order_details}

def route_after_triage(state: TicketState):
    triage = state["triage"]
    order = state.get("order_details") or {}
    amount = order.get("amount_inr", 0)

    # Pause for human approval if refund > ₹1000 or AI flagged it
    if triage.get("needs_human_approval") or (
        triage.get("intent") == "refund_request" and amount > 1000
    ):
        return "human_approval"
    return "finalize_action"

def human_approval(state: TicketState):
    # LangGraph pauses here and saves state until /approve is called
    decision = interrupt({
        "reason": "High-stakes action requires human approval",
        "triage": state["triage"],
        "order_details": state["order_details"],
    })
    return {"human_approved": decision.get("approved", False)}

def finalize_action(state: TicketState):
    triage = state["triage"]
    order = state.get("order_details") or {}

    if state.get("human_approved") is False:
        return {
            "final_status": "rejected_by_human",
            "final_reply": "We reviewed your request and cannot approve the refund at this time.",
        }

    status_note = f" (Order #{order.get('order_id')} is currently {order.get('status')})" if order and "order_id" in order else ""
    return {
        "final_status": "completed",
        "final_reply": f"{triage['draft_reply']}{status_note}",
    }

# Build & compile the graph with a Checkpointer
builder = StateGraph(TicketState)
builder.add_node("triage_and_lookup", triage_and_lookup)
builder.add_node("human_approval", human_approval)
builder.add_node("finalize_action", finalize_action)

builder.add_edge(START, "triage_and_lookup")
builder.add_conditional_edges("triage_and_lookup", route_after_triage)
builder.add_edge("human_approval", "finalize_action")
builder.add_edge("finalize_action", END)

agent_graph = builder.compile(checkpointer=MemorySaver())