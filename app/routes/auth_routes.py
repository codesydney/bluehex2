from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.controllers.auth_controller import AuthController
from app.models.user import UserCreate, UserLogin, PhoneCountry
from app.utils.auth import get_current_user_from_request
from fastapi.templating import Jinja2Templates
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Show login page."""
    user = await get_current_user_from_request(request, db)
    # If already logged in, redirect to home
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "user": None,
        "is_logged_in": False
    })

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle login."""
    try:
        auth_controller = AuthController(db)
        
        # Authenticate user
        user = await auth_controller.authenticate_user(email, password)
        
        if not user:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid email or password"
            })
        
        # Create session
        session_response = await auth_controller.create_session(user.id)
        
        # Send login notification
        await auth_controller.send_login_notification(user)
        
        # Set cookie and redirect
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token", 
            value=session_response.token, 
            httponly=True, 
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400
        )
        return response
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "An error occurred. Please try again."
        })

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Show signup page."""
    user = await get_current_user_from_request(request, db)
    # If already logged in, redirect to home
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("signup.html", {
        "request": request,
        "user": None,
        "is_logged_in": False
    })

@router.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    phone_country: str = Form(...),
    phone_number: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle signup."""
    try:
        # Validate password confirmation
        if password != confirm_password:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "Passwords do not match. Please try again."
            })
        
        auth_controller = AuthController(db)
        
        # Convert phone_country string to enum
        try:
            phone_country_enum = PhoneCountry(phone_country)
        except ValueError:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "Invalid country selected. Please try again."
            })
        
        # Create user data
        user_data = UserCreate(
            email=email.strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            password=password,
            phone_country=phone_country_enum,
            phone_number=phone_number.strip()
        )
        
        # Create user
        user = await auth_controller.create_user(user_data)
        
        # Auto-login: create session for the new user
        session_response = await auth_controller.create_session(user.id)
        
        # Set cookie and redirect to home
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token", 
            value=session_response.token, 
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400
        )
        return response
            
    except ValueError as e:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": str(e)
        })
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "An error occurred. Please try again."
        })

@router.get("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle logout."""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        auth_controller = AuthController(db)
        await auth_controller.delete_session(session_token)
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="session_token")
    return response

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Show forgot password page."""
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle forgot password request."""
    try:
        auth_controller = AuthController(db)
        success = await auth_controller.create_password_reset_token(email)
        
        # Always show success message for security (don't reveal if email exists)
        return templates.TemplateResponse("forgot-password.html", {
            "request": request,
            "success": "If an account with that email exists, we've sent you a password reset link."
        })
        
    except Exception as e:
        logger.error(f"Error in forgot password: {str(e)}", exc_info=True)
        return templates.TemplateResponse("forgot-password.html", {
            "request": request,
            "error": "An error occurred. Please try again."
        })

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = None):
    """Show reset password page."""
    # Get token from query params
    if not token:
        token = request.query_params.get("token")
    
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=302)
    
    return templates.TemplateResponse("reset-password.html", {
        "request": request,
        "token": token
    })

@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle password reset."""
    try:
        if new_password != confirm_password:
            return templates.TemplateResponse("reset-password.html", {
                "request": request,
                "token": token,
                "error": "Passwords do not match."
            })
        
        if len(new_password) < 8:
            return templates.TemplateResponse("reset-password.html", {
                "request": request,
                "token": token,
                "error": "Password must be at least 8 characters long."
            })
        
        auth_controller = AuthController(db)
        success = await auth_controller.reset_password(token, new_password)
        
        if success:
            return templates.TemplateResponse("reset-password.html", {
                "request": request,
                "success": "Password reset successfully! You can now log in with your new password."
            })
        else:
            return templates.TemplateResponse("reset-password.html", {
                "request": request,
                "token": token,
                "error": "Invalid or expired reset token. Please request a new password reset."
            })
        
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}", exc_info=True)
        return templates.TemplateResponse("reset-password.html", {
            "request": request,
            "token": token,
            "error": "An error occurred. Please try again."
        })

