from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from app.database import init_db, get_db
from app.utils.auth import get_current_user_from_request
from app.routes.auth_routes import router as auth_router
import logging
from dotenv import load_dotenv

# Import models to ensure they're registered with SQLModel before database initialization
from app.models.user import User, Session, PasswordResetToken  # noqa: F401

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}", exc_info=True)
        # Continue startup even if DB init fails (for development)
        pass
    yield
    # Shutdown: nothing yet

# Create FastAPI app
app = FastAPI(
    title="bluehex2",
    description="A FastAPI application with signup/signin functionality",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include auth routes
app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: AsyncSession = Depends(get_db)):
    """Root endpoint."""
    user = await get_current_user_from_request(request, db)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "is_logged_in": user is not None,
        "current_path": "/"
    })

@app.get("/customers-love-us", response_class=HTMLResponse)
async def customers_love_us_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Show customers love us page."""
    user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("customers-love-us.html", {
        "request": request,
        "user": user,
        "is_logged_in": user is not None,
        "current_path": "/customers-love-us"
    })

@app.get("/bluehex-blocks", response_class=HTMLResponse)
async def bluehex_blocks_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Show bluehex blocks page."""
    user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("bluehex-blocks.html", {
        "request": request,
        "user": user,
        "is_logged_in": user is not None,
        "current_path": "/bluehex-blocks"
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Show contact page."""
    user = await get_current_user_from_request(request, db)
    return templates.TemplateResponse("contact.html", {
        "request": request,
        "user": user,
        "is_logged_in": user is not None,
        "current_path": "/contact"
    })

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

