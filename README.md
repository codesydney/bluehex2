# bluehex2

A FastAPI application with signup/signin functionality, following the FastAPI MVC development guide.

## Features

- User authentication (signup/signin)
- Password reset functionality
- Email notifications (welcome, login, password reset)
- Session management with secure cookies
- Database persistence with SQLite (with Fly.io volume support)

## Project Structure

```
bluehex2/
├── app/
│   ├── __init__.py
│   ├── models/          # Database models (SQLModel)
│   │   └── user.py       # User, Session, PasswordResetToken models
│   ├── controllers/      # Business logic layer
│   │   └── auth_controller.py
│   ├── routes/           # API route definitions
│   │   └── auth_routes.py
│   ├── templates/        # Jinja2 templates with TailwindCSS
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── forgot-password.html
│   │   ├── reset-password.html
│   │   └── index.html
│   ├── utils/            # Utility functions
│   │   └── auth.py       # Authentication utilities
│   ├── services/         # External services
│   │   └── email_service.py
│   └── database.py       # Database configuration
├── main.py               # FastAPI application entry point
├── requirements.txt      # Dependencies
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Mailjet Configuration
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_SECRET_KEY=your_mailjet_secret_key
MAIL_FROM_EMAIL=noreply@example.com
MAIL_FROM_NAME=bluehex2
MAIL_ADMIN_EMAIL=admin@example.com

# Application Configuration
BASE_URL=http://localhost:8000
```

### 3. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Database

The application uses SQLite with async SQLAlchemy. The database file is created automatically on first run:

- **Development**: `./bluehex2.db`
- **Production (Fly.io)**: `/data/bluehex2.db` (uses persistent volume)

## Design System

This application follows the Vibecamp design system:

- **Colors**: Pure black (#000000) and white (#ffffff)
- **Typography**: 
  - Headings: Kalam (handwritten style)
  - Body: Inter (system font)
- **Borders**: 2px solid black borders
- **Footer**: "A Vibecamp Creation" attribution

## Email Configuration

Email notifications are sent using Mailjet. Configure your Mailjet API credentials in the `.env` file.

Email notifications include:
- Welcome email on signup
- Login notification
- Password reset email
- Password reset confirmation

## Routes

- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Handle login
- `GET /signup` - Signup page
- `POST /signup` - Handle signup
- `GET /logout` - Handle logout
- `GET /forgot-password` - Forgot password page
- `POST /forgot-password` - Request password reset
- `GET /reset-password` - Reset password page
- `POST /reset-password` - Handle password reset

## Security Features

- Password hashing with bcrypt
- Secure session tokens (cryptographically secure)
- HttpOnly cookies for session management
- Password reset tokens with expiration (1 hour)
- Input validation with Pydantic models

## Development

The application follows FastAPI MVC best practices:

- Clear separation of concerns (Models, Controllers, Routes)
- Async/await for all I/O operations
- Type hints throughout
- Error handling with proper HTTP status codes
- Mobile-first responsive design

## License

A Vibecamp Creation
