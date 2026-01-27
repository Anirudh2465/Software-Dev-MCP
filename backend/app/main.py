from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .services.orchestrator import JarvisOrchestrator

# Global Orchestrator Instance
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    orchestrator = JarvisOrchestrator()
    await orchestrator.start()
    print("Orchestrator started.")
    yield
    await orchestrator.stop()
    print("Orchestrator stopped.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ModeRequest(BaseModel):
    mode: str

@app.post("/chat")
async def chat(request: ChatRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    response = await orchestrator.process_message(request.message)
    return {"response": response}

@app.get("/history")
async def get_history():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    # Return last 10 messages for simplicity
    return {"history": orchestrator.messages[-10:]}

@app.post("/mode")
async def set_mode(request: ModeRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.prompt_manager.set_mode(request.mode)
    return {"status": result}

@app.get("/health")
async def health():
    return {"status": "ok"}
