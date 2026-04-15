"""
NexHost V6 - API Routes
=======================
FastAPI endpoints for all features
"""
from typing import List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from database import get_db, User, UserRole, ReadyBot, UserBot, BotStatus
from auth import (
    get_current_user, require_admin, require_superadmin,
    AuthService, create_access_token
)
from ai_router import ai_router, ai_chat, ai_code_fix, ai_code_explain
from ready_bots_service import (
    ready_bot_service, user_bot_service, ai_bot_generator
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ Pydantic Models ============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=8)
    role: Optional[UserRole] = UserRole.USER


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    max_python_files: int
    max_php_files: int
    max_ready_bots: int
    created_at: datetime
    last_login: Optional[datetime]


class AIChatRequest(BaseModel):
    message: str
    model: str = "v3"  # v3 or r1
    system_prompt: Optional[str] = None
    temperature: float = Field(0.7, ge=0, le=1)


class AIChatResponse(BaseModel):
    response: str
    model: str
    provider: str
    latency_ms: float
    cached: bool = False


class ReadyBotCreate(BaseModel):
    name: str
    description: str
    bot_type: str = "telegram"
    code: str
    requirements: str
    image_url: Optional[str] = None
    icon: str = "🤖"
    config_fields: Optional[List[dict]] = None
    is_premium: bool = False


class ReadyBotResponse(BaseModel):
    id: int
    name: str
    description: str
    bot_type: str
    image_url: Optional[str]
    icon: str
    is_active: bool
    is_premium: bool
    config_fields: List[dict]
    created_at: datetime


class UserBotCreate(BaseModel):
    template_id: int
    name: str
    config: dict
    debug_mode: bool = False


class BotGenerateRequest(BaseModel):
    description: str
    bot_type: str = "telegram"
    features: Optional[List[str]] = None


class CodeDebugRequest(BaseModel):
    code: str
    error_message: Optional[str] = None


class QuotaUpdateRequest(BaseModel):
    max_python_files: Optional[int] = None
    max_php_files: Optional[int] = None
    max_ready_bots: Optional[int] = None


# ============ Auth Routes ============

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user"""
    user = await AuthService.authenticate_user(db, request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    tokens = AuthService.generate_tokens(user)
    
    return {
        **tokens,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value
        }
    }


@router.post("/auth/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    new_token = create_access_token({
        "sub": current_user.username,
        "user_id": current_user.id,
        "role": current_user.role.value
    })
    
    return {"access_token": new_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "max_python_files": current_user.max_python_files,
        "max_php_files": current_user.max_php_files,
        "max_ready_bots": current_user.max_ready_bots,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


# ============ Admin Routes ============

@router.post("/admin/users", response_model=UserResponse)
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create new user (Admin only)"""
    user = await AuthService.create_user(
        db,
        username=request.username,
        email=request.email,
        password=request.password,
        role=request.role
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "max_python_files": user.max_python_files,
        "max_php_files": user.max_php_files,
        "max_ready_bots": user.max_ready_bots,
        "created_at": user.created_at,
        "last_login": user.last_login
    }


@router.get("/admin/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all users (Admin only)"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role.value,
            "is_active": u.is_active,
            "max_python_files": u.max_python_files,
            "max_php_files": u.max_php_files,
            "max_ready_bots": u.max_ready_bots,
            "created_at": u.created_at,
            "last_login": u.last_login
        }
        for u in users
    ]


@router.patch("/admin/users/{user_id}/quotas")
async def update_user_quotas(
    user_id: int,
    request: QuotaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update user quotas (Admin only)"""
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.max_python_files is not None:
        user.max_python_files = request.max_python_files
    if request.max_php_files is not None:
        user.max_php_files = request.max_php_files
    if request.max_ready_bots is not None:
        user.max_ready_bots = request.max_ready_bots
    
    await db.commit()
    
    return {"message": "Quotas updated successfully"}


# ============ AI Routes ============

@router.post("/ai/chat", response_model=AIChatResponse)
async def chat(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat with AI"""
    from ai_router import AIModel
    
    model = AIModel.V3 if request.model == "v3" else AIModel.R1
    
    response = await ai_router.generate(
        prompt=request.message,
        model=model,
        system_prompt=request.system_prompt,
        temperature=request.temperature
    )
    
    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.error or "AI service unavailable"
        )
    
    return {
        "response": response.content,
        "model": response.model,
        "provider": response.provider,
        "latency_ms": response.latency_ms,
        "cached": response.cached
    }


@router.post("/ai/code/fix")
async def fix_code(
    request: CodeDebugRequest,
    current_user: User = Depends(get_current_user)
):
    """Fix code using AI"""
    try:
        fixed_code = await ai_code_fix(request.code)
        return {"fixed_code": fixed_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/code/explain")
async def explain_code(
    request: CodeDebugRequest,
    current_user: User = Depends(get_current_user)
):
    """Explain code using AI"""
    try:
        explanation = await ai_code_explain(request.code)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/status")
async def ai_status(current_user: User = Depends(get_current_user)):
    """Get AI service status"""
    health = await ai_router.health_check_all()
    stats = ai_router.get_stats()
    
    return {
        "health": health,
        "stats": stats
    }


# ============ Ready Bots Routes (Admin) ============

@router.post("/admin/ready-bots", response_model=ReadyBotResponse)
async def create_ready_bot(
    request: ReadyBotCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create ready bot template (Admin only)"""
    bot = await ready_bot_service.create_bot_template(
        db=db,
        name=request.name,
        description=request.description,
        bot_type=request.bot_type,
        code=request.code,
        requirements=request.requirements,
        created_by=admin.id,
        image_url=request.image_url,
        icon=request.icon,
        config_fields=request.config_fields,
        is_premium=request.is_premium
    )
    
    return {
        "id": bot.id,
        "name": bot.name,
        "description": bot.description,
        "bot_type": bot.bot_type,
        "image_url": bot.image_url,
        "icon": bot.icon,
        "is_active": bot.is_active,
        "is_premium": bot.is_premium,
        "config_fields": bot.config_fields or [],
        "created_at": bot.created_at
    }


@router.get("/admin/ready-bots")
async def list_ready_bots(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all ready bot templates (Admin only)"""
    bots = await ready_bot_service.get_all_templates(db, include_inactive=True)
    
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "bot_type": b.bot_type,
            "image_url": b.image_url,
            "icon": b.icon,
            "is_active": b.is_active,
            "is_premium": b.is_premium,
            "config_fields": b.config_fields or [],
            "created_at": b.created_at
        }
        for b in bots
    ]


@router.delete("/admin/ready-bots/{bot_id}")
async def delete_ready_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete ready bot template (Admin only)"""
    success = await ready_bot_service.delete_template(db, bot_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bot template not found")
    
    return {"message": "Bot template deleted successfully"}


# ============ User Bots Routes ============

@router.get("/ready-bots")
async def list_available_bots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available ready bots for users"""
    bots = await ready_bot_service.get_all_templates(db, include_inactive=False)
    
    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "bot_type": b.bot_type,
            "image_url": b.image_url,
            "icon": b.icon,
            "is_premium": b.is_premium,
            "config_fields": b.config_fields or []
        }
        for b in bots
    ]


@router.post("/my-bots")
async def create_user_bot(
    request: UserBotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create bot instance from template"""
    try:
        bot = await user_bot_service.create_bot_instance(
            db=db,
            user=current_user,
            template_id=request.template_id,
            name=request.name,
            config=request.config,
            debug_mode=request.debug_mode
        )
        
        return {
            "id": bot.id,
            "name": bot.name,
            "status": bot.status.value,
            "template_id": bot.bot_template_id,
            "created_at": bot.created_at
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-bots")
async def list_my_bots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's bot instances"""
    bots = await user_bot_service.get_user_bots(db, current_user.id)
    
    return [
        {
            "id": b.id,
            "name": b.name,
            "status": b.status.value,
            "template_name": b.template.name if b.template else None,
            "debug_mode": b.debug_mode,
            "created_at": b.created_at,
            "started_at": b.started_at
        }
        for b in bots
    ]


@router.post("/my-bots/{bot_id}/start")
async def start_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start bot instance"""
    bot = await user_bot_service.get_bot(db, bot_id, current_user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    success = await user_bot_service.start_bot(bot)
    
    if success:
        await db.commit()
        return {"message": "Bot started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start bot")


@router.post("/my-bots/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop bot instance"""
    bot = await user_bot_service.get_bot(db, bot_id, current_user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    success = await user_bot_service.stop_bot(bot)
    
    if success:
        await db.commit()
        return {"message": "Bot stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop bot")


@router.get("/my-bots/{bot_id}/logs")
async def get_bot_logs(
    bot_id: int,
    lines: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get bot logs"""
    bot = await user_bot_service.get_bot(db, bot_id, current_user.id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    logs = await user_bot_service.get_bot_logs(bot, lines)
    
    return {"logs": logs}


@router.delete("/my-bots/{bot_id}")
async def delete_my_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete bot instance"""
    success = await user_bot_service.delete_bot(db, bot_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {"message": "Bot deleted successfully"}


# ============ AI Bot Generator Routes ============

@router.post("/ai/generate-bot")
async def generate_bot(
    request: BotGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate bot using AI"""
    try:
        result = await ai_bot_generator.generate_bot(
            description=request.description,
            bot_type=request.bot_type,
            features=request.features
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/debug-bot")
async def debug_bot(
    request: CodeDebugRequest,
    current_user: User = Depends(get_current_user)
):
    """Debug bot code using AI"""
    try:
        fixed_code = await ai_bot_generator.debug_code(
            code=request.code,
            error_message=request.error_message
        )
        
        return {"fixed_code": fixed_code}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Health Check ============

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "6.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
