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
    # Return current mode as well so UI can sync if tool changed it
    return {"response": response, "current_mode": orchestrator.prompt_manager.mode}

@app.get("/history")
async def get_history():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    return {"history": orchestrator.messages[-10:]}

@app.post("/mode")
async def set_mode(request: ModeRequest):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.prompt_manager.set_mode(request.mode)
    return {"status": result, "mode": orchestrator.prompt_manager.mode}

@app.get("/modes")
async def get_modes():
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    # Fetch distinct modes from Memory
    modes = orchestrator.semantic_memory.get_modes()
    return {"modes": modes, "current_mode": orchestrator.prompt_manager.mode}

@app.delete("/modes/{mode_name}")
async def delete_mode(mode_name: str):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    if mode_name == "Work":
        return {"status": "Cannot delete default 'Work' mode."}
        
    orchestrator.semantic_memory.delete_mode(mode_name)
    orchestrator.episodic_memory.delete_mode_memory(mode_name)
    
    # If we deleted current mode, switch to Work
    if orchestrator.prompt_manager.mode == mode_name:
        orchestrator.prompt_manager.set_mode("Work")
        
    return {"status": f"Deleted mode {mode_name}"}

@app.get("/memory/{mode_name}")
async def get_memory(mode_name: str):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    facts = orchestrator.semantic_memory.get_all_facts(mode=mode_name)
    return {"facts": facts}

@app.get("/health")
async def health():
    return {"status": "ok"}
