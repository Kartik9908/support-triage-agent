# Support Triage Agent (LangGraph + MCP)

An Agentic AI Customer Support & Order Triage backend that classifies incoming customer tickets, queries live order data from PostgreSQL via Model Context Protocol (MCP), and pauses for **Human-in-the-Loop (HITL)** approval on high-value refunds.

**Live API Docs (Swagger UI):** https://support-triage-agent-gb8t.onrender.com/docs

---

## Key Features
- **Structured AI Triage:** Uses Google Gemini (`gemini-3.0-flash`) with Pydantic schemas to extract intent, order ID, urgency, and draft replies.
- **Live Database Tooling (MCP):** Exposes PostgreSQL order lookups through an `MCPServer` tool connected to Neon cloud PostgreSQL.
- **Human-in-the-Loop (LangGraph):** Uses `MemorySaver` checkpointing and `interrupt()` to pause execution whenever a refund exceeds ₹1,000 or requires manual review, then resumes seamlessly once approved or rejected.
- **Production REST API:** Built with FastAPI and deployed on Render.

---

## Tech Stack
- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **AI & Orchestration:** LangGraph, Google Gemini API (`gemini-3.0-flash`)
- **Tooling & Database:** Model Context Protocol (MCP), Neon PostgreSQL (`psycopg2`)
- **Deployment:** Render, GitHub

---

## API Endpoints

### 1. `POST /triage`
Analyzes a customer message, checks live order status, and either completes the reply or pauses with a `thread_id` for human approval.

**Sample Request:**
```json
{
  "customer_email": "aarav@example.com",
  "message": "Where is my order 4021? It is delayed and I want a full refund!"
}
