import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("SupportDatabase")

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

@mcp.tool()
def get_order_status(order_id: int) -> dict:
    """Fetch order details and shipping status from PostgreSQL by order ID."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT o.order_id, o.item_name, o.amount_inr, o.status, c.name, c.email
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.order_id = %s
                    """,
                    (order_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else {"error": f"Order {order_id} not found"}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

if __name__ == "__main__":
    mcp.run()