import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.types import Command
from app.schemas import TicketInput
from app.agent import agent_graph

app = FastAPI(title="Support Triage Agent (LangGraph + MCP)")

class ApprovalInput(BaseModel):
    approved: bool

@app.post("/triage")
def triage_ticket(ticket: TicketInput):
    thread_id = str(uuid.uuid4())[:8]
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = agent_graph.invoke(
            {"customer_email": ticket.customer_email, "message": ticket.message},
            config=config,
        )
        # Check if the graph paused at the Human-in-the-Loop interrupt
        state = agent_graph.get_state(config)
        if state.next:
            return {
                "thread_id": thread_id,
                "status": "awaiting_human_approval",
                "pending_review": state.tasks[0].interrupts[0].value,
            }
        return {
            "thread_id": thread_id,
            "status": result["final_status"],
            "order_details": result.get("order_details"),
            "reply": result["final_reply"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")

@app.post("/approve/{thread_id}")
def approve_ticket(thread_id: str, decision: ApprovalInput):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = agent_graph.invoke(
            Command(resume={"approved": decision.approved}),
            config=config,
        )
        return {
            "thread_id": thread_id,
            "status": result["final_status"],
            "reply": result["final_reply"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")