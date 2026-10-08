from fastapi import FastAPI
from pydantic import BaseModel
from agent import run_agent

app = FastAPI(
    title="ShopUNow Agentic AI Assistant",
    description="A strong RAG AI Assistant for HR, IT Support, Billing, and Shipping.",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default"

class QueryResponse(BaseModel):
    response: str
    department: str
    sentiment: str

@app.post("/query", response_model=QueryResponse)
async def query_assistant(request: QueryRequest):
 
   result = run_agent(
        query=request.query,
        session_id=request.session_id
    )
    
    return QueryResponse(
        response=result.get("response", "Error processing request."),
        department=result.get("department", "Unknown"),
        sentiment=result.get("sentiment", "Unknown")
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
