import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ensure parent directory is in path so we can import router and providers modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from router.intelligent_router import IntelligentRouter

from prometheus_client import make_asgi_app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI(
    title="LLM Cost Autopilot API",
    description="Intelligent LLM Gateway that routes prompts based on complexity to save inference costs.",
    version="1.0.0"
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Initialize Intelligent Router
# Config path defaults to models.yaml in root folder
try:
    router = IntelligentRouter(models_config_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../models.yaml")))
except Exception as e:
    print(f"Error loading IntelligentRouter: {e}")
    router = None

class ChatRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    log_id: Optional[int] = None
    response: str
    complexity_label: str
    complexity_score: float
    model_used: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    savings: float
    explanation: Optional[Dict[str, float]] = None

class FeedbackRequest(BaseModel):
    log_id: int
    feedback: str

@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not router:
        raise HTTPException(status_code=500, detail="Intelligent Router is not initialized correctly.")
    
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    try:
        result = await router.route(request.prompt, request.system_prompt)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing or LLM execution error: {str(e)}")

@app.post("/v1/feedback")
def feedback(request: FeedbackRequest):
    if not router or not router.cache:
        raise HTTPException(status_code=500, detail="Database/Cache is not initialized.")
    success = router.cache.update_feedback(request.log_id, request.feedback)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to update feedback for log id {request.log_id}")
    return {"status": "success", "detail": "Feedback updated successfully."}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "router_initialized": router is not None
    }
