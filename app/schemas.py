from pydantic import BaseModel, Field
from typing import Optional, Literal

class TicketInput(BaseModel):
    customer_email: str
    message: str

class TriageResult(BaseModel):
    intent: Literal["order_status", "refund_request", "general_inquiry"]
    order_id: Optional[int] = Field(None, description="Extracted order ID if mentioned")
    urgency: Literal["low", "medium", "high"]
    needs_human_approval: bool = Field(
        description="True if refund is requested or customer is angry"
    )
    draft_reply: str