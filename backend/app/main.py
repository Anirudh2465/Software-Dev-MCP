from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Annotated, List
from datetime import timedelta

from .services.orchestrator import JarvisOrchestrator
from .services.auth import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from .services.chat_service import ChatService
from .schemas.auth import UserCreate, UserLogin, Token, User, TokenData

# Global Instances
orchestrator = None
auth_service = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencies ---
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth_service.verify_token(token) if hasattr(auth_service, 'verify_token') else None
        # Since I didn't export verify_token in AuthService, let's decode here or update AuthService.
        # simpler: just use jose here or update AuthService. I'll use jose here for speed or verify_token if I added it?
        # I didn't add verify_token to AuthService in previous step. I'll do it manually here.
        from jose import JWTError, jwt
        from .services.auth import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = auth_service.get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# --- Auth Routes ---

# --- Auth Routes ---

@app.post("/auth/signup", response_model=UserCreate)
def signup(user: UserCreate):
    db_user = auth_service.create_user(user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Trigger Celery Task (Background)
    from .tasks import initialize_user_partition
    initialize_user_partition.delay(user.username)
    
    return user

@app.post("/auth/login", response_model=Token)
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = auth_service.get_user(form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return {"username": current_user["username"]}


# --- App Routes ---

class ChatRequest(BaseModel):
    message: str
    chat_id: str

class CreateChatRequest(BaseModel):
    title: str
    mode: str = "Work"

class ModeRequest(BaseModel):
    mode: str

class PersonaRequest(BaseModel):
    persona: str

@app.post("/chat")
async def chat(request: ChatRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    # process_message now takes user_id and chat_id
    response = await orchestrator.process_message(
        request.message, 
        user_id=current_user["username"], 
        chat_id=request.chat_id
    )
    return {"response": response, "current_mode": orchestrator.prompt_manager.mode}

@app.get("/chats")
def get_chats(current_user: Annotated[dict, Depends(get_current_user)], mode: str = "Work"):
    chat_service = ChatService()
    return chat_service.get_chats(current_user["username"], mode)

@app.post("/chats")
def create_chat(request: CreateChatRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    chat_service = ChatService()
    return chat_service.create_chat(current_user["username"], request.mode, request.title)

@app.get("/chats/{chat_id}")
def get_chat(chat_id: str, current_user: Annotated[dict, Depends(get_current_user)]):
    chat_service = ChatService()
    chat = chat_service.get_chat(chat_id, current_user["username"])
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, current_user: Annotated[dict, Depends(get_current_user)]):
    chat_service = ChatService()
    success = chat_service.delete_chat(chat_id, current_user["username"])
    if not success:
         raise HTTPException(status_code=404, detail="Chat not found or could not be deleted")
    return {"status": "deleted"}

@app.get("/history")
async def get_history(current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    # For now history is global in orchestrator.. we might need to filter by user too?
    # Orchestrator keeps a living history. If we want per-user session, we need to restructure further.
    # For now, let's just return global history or empty if we move to stateless.
    # Given the requirements, let's just return what's there but note it might be shared if not careful.
    # Actually, `orchestrator.messages` is in-memory. If we have multiple users, this is bad.
    # BUT, the request was just about "database partition". 
    # For a proper multi-user app, we need one orchestrator per user or a session manager.
    # Let's stick to the requested "database partition".
    # return {"history": orchestrator.messages[-10:]} 
    # History is now managed via /chats/{chat_id}
    return {"message": "Use /chats/{chat_id} to get history."}

@app.delete("/history")
async def clear_history(current_user: Annotated[dict, Depends(get_current_user)]):
    # This endpoint is deprecated in favor of deleting specific chats, but we'll keep it as a no-op or clear global?
    # Actually, with stateless orchestrator, there is no 'global history' in memory to clear.
    return {"status": "History is now managed per chat session. Delete the chat instead."}

@app.post("/mode")
async def set_mode(request: ModeRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    # This changes global mode... 
    # We should probably pass user_id to set_mode if we want per-user mode?
    # PromptManager is part of Orchestrator instance. 
    # This reveals Orchestrator is a singleton.
    # For this task, I will just proceed with the requested DB changes.
    result = orchestrator.prompt_manager.set_mode(request.mode)
    return {"status": result, "mode": orchestrator.prompt_manager.mode}

@app.post("/persona")
async def set_persona(request: PersonaRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.prompt_manager.set_persona(request.persona)
    return {"status": result, "persona": orchestrator.prompt_manager.persona}

@app.get("/modes")
async def get_modes(current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    modes = orchestrator.mode_manager.get_all_modes()
    return {"modes": modes, "current_mode": orchestrator.prompt_manager.mode}

@app.delete("/modes/{mode_name}")
async def delete_mode(mode_name: str, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.mode_manager.delete_mode(mode_name)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    # Also delete memory
    orchestrator.semantic_memory.delete_mode(mode_name, user_id=current_user["username"])
    orchestrator.episodic_memory.delete_mode_memory(mode_name, user_id=current_user["username"])
    
    if orchestrator.prompt_manager.mode == mode_name:
        orchestrator.prompt_manager.set_mode("Work")
        
    return result

# --- Tone Routes ---

class ToneRequest(BaseModel):
    tone: str

class CreateToneRequest(BaseModel):
    name: str
    description: str

@app.get("/tones")
async def get_tones(current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    tones = orchestrator.tone_manager.get_all_tones()
    return {"tones": tones, "current_tone": orchestrator.prompt_manager.tone}

@app.post("/tones")
async def create_tone(request: CreateToneRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.tone_manager.create_tone(request.name, request.description)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.delete("/tones/{tone_name}")
async def delete_tone(tone_name: str, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.tone_manager.delete_tone(tone_name)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    # Reset to default if deleted tone was active
    if orchestrator.prompt_manager.tone == tone_name:
        orchestrator.prompt_manager.set_tone("Professional")
        
    return result

@app.post("/tone")
async def set_tone(request: ToneRequest, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    result = orchestrator.prompt_manager.set_tone(request.tone)
    return {"status": result, "tone": orchestrator.prompt_manager.tone}

@app.get("/memory/{mode_name}")
async def get_memory(mode_name: str, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
         raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    facts = orchestrator.semantic_memory.get_all_facts(mode=mode_name, user_id=current_user["username"])
    episodes = orchestrator.episodic_memory.get_all_episodes(mode=mode_name, user_id=current_user["username"])
    return {"semantic": facts, "episodic": episodes}

@app.delete("/memory/semantic/{fact_id}")
async def delete_semantic_memory(fact_id: str, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    # Note: delete_fact in MemoryManager returns result document or None
    deleted_doc = orchestrator.semantic_memory.delete_fact(fact_id)
    
    if not deleted_doc:
         raise HTTPException(status_code=404, detail="Fact not found or could not be deleted")
         
    # HARD DELETE: Remove traces from episodic memory
    fact_content = deleted_doc.get("fact")
    if fact_content:
        # We delete any episode that contains this exact fact text.
        # This covers "Saved: [fact]" messages if the text matches.
        deleted_count = orchestrator.episodic_memory.delete_episodes_containing(
            text=fact_content, 
            mode=deleted_doc.get("mode", "Work"),
            user_id=current_user["username"]
        )
        print(f"Also deleted {deleted_count} related episodic memories.")
        
    return {"status": "deleted", "related_episodes_deleted": deleted_count if 'deleted_count' in locals() else 0}

@app.delete("/memory/episodic/{episode_id}")
async def delete_episodic_memory(episode_id: str, mode: str, current_user: Annotated[dict, Depends(get_current_user)]):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not ready")
    
    success = orchestrator.episodic_memory.delete_episode(episode_id, mode=mode, user_id=current_user["username"])
    if not success:
         raise HTTPException(status_code=404, detail="Episode not found or could not be deleted")
    return {"status": "deleted"}

@app.get("/health")
async def health():
    return {"status": "ok"}
