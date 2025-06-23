"""
Email Service for sending verification and reset emails
"""
import smtplib
import secrets
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', self.smtp_username)
        self.from_name = getattr(settings, 'FROM_NAME', 'ScapeGIS')
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, to_email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
        """Send email verification email"""
        
        verification_url = f"{settings.FRONTEND_URL}/verify?token={verification_token}"
        
        subject = "Verify Your ScapeGIS Account"
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Account</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to ScapeGIS!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                <h2 style="color: #333; margin-top: 0;">Verify Your Email Address</h2>
                
                <p>Hi {user_name or 'there'},</p>
                
                <p>Thank you for signing up for ScapeGIS! To complete your registration and start using our GIS platform, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace;">
                    {verification_url}
                </p>
                
                <p><strong>This verification link will expire in 24 hours.</strong></p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't create an account with ScapeGIS, you can safely ignore this email.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Best regards,<br>
                    The ScapeGIS Team
                </p>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        Welcome to ScapeGIS!
        
        Hi {user_name or 'there'},
        
        Thank you for signing up for ScapeGIS! To complete your registration, please verify your email address by visiting this link:
        
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with ScapeGIS, you can safely ignore this email.
        
        Best regards,
        The ScapeGIS Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
        """Send password reset email"""
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Reset Your ScapeGIS Password"
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
                
                <p>Hi {user_name or 'there'},</p>
                
                <p>We received a request to reset your ScapeGIS account password. Click the button below to create a new password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 5px; font-family: monospace;">
                    {reset_url}
                </p>
                
                <p><strong>This reset link will expire in 1 hour.</strong></p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Best regards,<br>
                    The ScapeGIS Team
                </p>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        Password Reset - ScapeGIS
        
        Hi {user_name or 'there'},
        
        We received a request to reset your ScapeGIS account password. Visit this link to create a new password:
        
        {reset_url}
        
        This reset link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        Best regards,
        The ScapeGIS Team
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_token_expiry(hours: int = 24) -> datetime:
        """Get token expiry datetime"""
        return datetime.utcnow() + timedelta(hours=hours)


# Global email service instance
email_service = EmailService()
