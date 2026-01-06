from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.auth_controller import AuthController
from app.models.user import UserResponse

async def get_current_user_from_request(
    request: Request, 
    db: AsyncSession
) -> Optional[UserResponse]:
    """Get current user from session token in request cookies."""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return None
    
    try:
        auth_controller = AuthController(db)
        session_response = await auth_controller.get_session_by_token(session_token)
        
        if session_response:
            return session_response.user
    except Exception:
        pass
    
    return None

