import os
from mailjet_rest import Client
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Mailjet API credentials (read from env)
        self.api_key = os.getenv("MAILJET_API_KEY", "")
        self.secret_key = os.getenv("MAILJET_SECRET_KEY", "")
        
        # Validate credentials
        if not self.api_key or not self.secret_key:
            logger.warning("Mailjet API credentials not fully configured. Email sending will fail.")
        
        self.mailjet = Client(auth=(self.api_key, self.secret_key), version='v3.1')
        # Use verified sender
        self.from_email = os.getenv("MAIL_FROM_EMAIL", "noreply@example.com")
        self.from_name = os.getenv("MAIL_FROM_NAME", "Bluehex2")
        
        # Admin email for CC on notifications
        self.admin_email = os.getenv("MAIL_ADMIN_EMAIL", "")
        
        # Base URL for email links (defaults to localhost for development)
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    async def _send_mailjet_request(self, data: dict):
        """Helper method to run synchronous Mailjet calls in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.mailjet.send.create(data=data)
        )

    async def send_welcome_email(self, to_email: str, first_name: str) -> bool:
        """Send welcome email after signup."""
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": f"Welcome to {self.from_name}",
                        "TextPart": f"Hi {first_name},\n\nWelcome to {self.from_name}! We're excited to have you join our community.\n\nBest regards,\nThe {self.from_name} Team",
                        "HTMLPart": f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="padding: 40px 20px; background: #ffffff; border-bottom: 2px solid #000000;">
                                <h1 style="color: #000000; margin: 0; font-size: 24px; font-weight: bold;">Welcome to {self.from_name}</h1>
                            </div>
                            <div style="padding: 40px 20px; background: #ffffff;">
                                <h2 style="color: #000000; margin-bottom: 20px; font-size: 18px;">Hi {first_name},</h2>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 20px;">
                                    Welcome to {self.from_name}! We're excited to have you join our community.
                                </p>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 30px;">
                                    You can now explore our platform and connect with other members.
                                </p>
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{self.base_url}/" 
                                       style="background: #000000; color: #ffffff; padding: 12px 30px; text-decoration: none; border: 2px solid #000000; display: inline-block; font-weight: bold;">
                                        Get Started
                                    </a>
                                </div>
                                <p style="color: #6B7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                                    Best regards,<br>
                                    The {self.from_name} Team
                                </p>
                            </div>
                        </div>
                        """
                    }
                ]
            }
            
            result = await self._send_mailjet_request(data)
            ok = result.status_code == 200
            if not ok:
                try:
                    logger.error(f"Welcome email failed: status={result.status_code} body={result.json()}")
                except Exception:
                    logger.error("Welcome email failed and response body was not JSON")
            else:
                logger.info(f"Welcome email sent to {to_email}: {result.status_code}")
            return ok
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
            return False

    async def send_login_notification(self, to_email: str, first_name: str, login_time: str) -> bool:
        """Send login notification email."""
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": f"New Login to Your {self.from_name} Account",
                        "TextPart": f"Hi {first_name},\n\nWe noticed a new login to your {self.from_name} account at {login_time}.\n\nIf this wasn't you, please secure your account immediately.\n\nBest regards,\nThe {self.from_name} Team",
                        "HTMLPart": f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="padding: 40px 20px; background: #ffffff; border-bottom: 2px solid #000000;">
                                <h1 style="color: #000000; margin: 0; font-size: 24px; font-weight: bold;">Account Activity</h1>
                            </div>
                            <div style="padding: 40px 20px; background: #ffffff;">
                                <h2 style="color: #000000; margin-bottom: 20px; font-size: 18px;">Hi {first_name},</h2>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 20px;">
                                    We noticed a new login to your {self.from_name} account:
                                </p>
                                <div style="background: #f9fafb; padding: 20px; border: 2px solid #000000; margin: 20px 0;">
                                    <p style="margin: 0; color: #000000; font-weight: bold;">Login Time: {login_time}</p>
                                </div>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 20px;">
                                    If this wasn't you, please secure your account immediately by changing your password.
                                </p>
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{self.base_url}/login" 
                                       style="background: #000000; color: #ffffff; padding: 12px 30px; text-decoration: none; border: 2px solid #000000; display: inline-block; font-weight: bold;">
                                        Secure My Account
                                    </a>
                                </div>
                                <p style="color: #6B7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                                    Best regards,<br>
                                    The {self.from_name} Security Team
                                </p>
                            </div>
                        </div>
                        """
                    }
                ]
            }
            
            result = await self._send_mailjet_request(data)
            ok = result.status_code == 200
            if not ok:
                try:
                    logger.error(f"Login email failed: status={result.status_code} body={result.json()}")
                except Exception:
                    logger.error("Login email failed and response body was not JSON")
            else:
                logger.info(f"Login notification sent to {to_email}: {result.status_code}")
            return ok
            
        except Exception as e:
            logger.error(f"Failed to send login notification to {to_email}: {str(e)}")
            return False

    async def send_password_reset_email(self, to_email: str, first_name: str, reset_token: str) -> bool:
        """Send password reset email."""
        if not self.api_key or not self.secret_key:
            logger.error("Mailjet credentials not configured. Cannot send password reset email.")
            return False
        
        try:
            reset_url = f"{self.base_url}/reset-password?token={reset_token}"
            
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": f"Reset Your {self.from_name} Password",
                        "TextPart": f"Hi {first_name},\n\nYou requested to reset your password. Click the link below to reset it:\n\n{reset_url}\n\nThis link will expire in 1 hour.\n\nIf you didn't request this, please ignore this email.\n\nBest regards,\nThe {self.from_name} Team",
                        "HTMLPart": f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="padding: 40px 20px; background: #ffffff; border-bottom: 2px solid #000000;">
                                <h1 style="color: #000000; margin: 0; font-size: 24px; font-weight: bold;">Password Reset</h1>
                            </div>
                            <div style="padding: 40px 20px; background: #ffffff;">
                                <h2 style="color: #000000; margin-bottom: 20px; font-size: 18px;">Hi {first_name},</h2>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 20px;">
                                    You requested to reset your password. Click the button below to reset it:
                                </p>
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{reset_url}" 
                                       style="background: #000000; color: #ffffff; padding: 15px 40px; text-decoration: none; border: 2px solid #000000; display: inline-block; font-weight: bold;">
                                        Reset My Password
                                    </a>
                                </div>
                                <p style="color: #6B7280; font-size: 14px; margin-top: 20px;">
                                    This link will expire in 1 hour for security reasons.
                                </p>
                                <p style="color: #000000; line-height: 1.6; margin-top: 30px;">
                                    If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                                </p>
                                <p style="color: #6B7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                                    Best regards,<br>
                                    The {self.from_name} Team
                                </p>
                            </div>
                        </div>
                        """
                    }
                ]
            }
            
            logger.info(f"Attempting to send password reset email to {to_email} using Mailjet...")
            result = await self._send_mailjet_request(data)
            ok = result.status_code == 200
            
            if not ok:
                try:
                    error_body = result.json()
                    logger.error(f"Password reset email failed: status={result.status_code}, body={error_body}")
                except Exception as e:
                    logger.error(f"Password reset email failed: status={result.status_code}, could not parse response: {e}")
            else:
                logger.info(f"Password reset email sent successfully to {to_email}")
            
            return ok
            
        except Exception as e:
            logger.error(f"Exception sending password reset email to {to_email}: {str(e)}", exc_info=True)
            return False

    async def send_password_reset_confirmation(self, to_email: str, first_name: str) -> bool:
        """Send confirmation email after password reset."""
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": first_name
                            }
                        ],
                        "Subject": f"Password Successfully Reset - {self.from_name}",
                        "TextPart": f"Hi {first_name},\n\nYour password has been successfully reset.\n\nIf you didn't make this change, please contact us immediately.\n\nBest regards,\nThe {self.from_name} Team",
                        "HTMLPart": f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="padding: 40px 20px; background: #ffffff; border-bottom: 2px solid #000000;">
                                <h1 style="color: #000000; margin: 0; font-size: 24px; font-weight: bold;">Password Reset Complete</h1>
                            </div>
                            <div style="padding: 40px 20px; background: #ffffff;">
                                <h2 style="color: #000000; margin-bottom: 20px; font-size: 18px;">Hi {first_name},</h2>
                                <p style="color: #000000; line-height: 1.6; margin-bottom: 20px;">
                                    Your password has been successfully reset. You can now log in with your new password.
                                </p>
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{self.base_url}/login" 
                                       style="background: #000000; color: #ffffff; padding: 12px 30px; text-decoration: none; border: 2px solid #000000; display: inline-block; font-weight: bold;">
                                        Sign In Now
                                    </a>
                                </div>
                                <p style="color: #000000; line-height: 1.6; margin-top: 30px; font-weight: bold;">
                                    If you didn't make this change, please contact us immediately.
                                </p>
                                <p style="color: #6B7280; font-size: 14px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                                    Best regards,<br>
                                    The {self.from_name} Security Team
                                </p>
                            </div>
                        </div>
                        """
                    }
                ]
            }
            
            result = await self._send_mailjet_request(data)
            ok = result.status_code == 200
            if not ok:
                try:
                    logger.error(f"Password reset confirmation failed: status={result.status_code} body={result.json()}")
                except Exception:
                    logger.error("Password reset confirmation failed and response body was not JSON")
            else:
                logger.info(f"Password reset confirmation sent to {to_email}: {result.status_code}")
            return ok
            
        except Exception as e:
            logger.error(f"Failed to send password reset confirmation to {to_email}: {str(e)}")
            return False

