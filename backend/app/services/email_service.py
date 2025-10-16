"""
Email service for VoyagerAI
Handles email verification, password reset, and notifications
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None) -> bool:
        """Send email using SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return False
                
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
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
    
    def send_verification_email(self, user_email: str, user_name: str, verification_token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
        
        subject = "Verify your VoyagerAI account"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Welcome to VoyagerAI!</h2>
            <p>Hi {user_name},</p>
            <p>Thank you for signing up for VoyagerAI. Please verify your email address to complete your registration.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>The VoyagerAI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to VoyagerAI!
        
        Hi {user_name},
        
        Thank you for signing up for VoyagerAI. Please verify your email address to complete your registration.
        
        Click this link to verify: {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        The VoyagerAI Team
        """
        
        return self._send_email(user_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, user_email: str, user_name: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        subject = "Reset your VoyagerAI password"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Password Reset Request</h2>
            <p>Hi {user_name},</p>
            <p>We received a request to reset your password for your VoyagerAI account.</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #dc2626; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>Best regards,<br>The VoyagerAI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user_name},
        
        We received a request to reset your password for your VoyagerAI account.
        
        Click this link to reset: {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        The VoyagerAI Team
        """
        
        return self._send_email(user_email, subject, html_content, text_content)
    
    def send_event_reminder_email(self, user_email: str, user_name: str, event_title: str, 
                                 event_date: str, event_venue: str, event_url: str = None) -> bool:
        """Send event reminder email"""
        subject = f"Reminder: {event_title} is tomorrow!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Event Reminder</h2>
            <p>Hi {user_name},</p>
            <p>This is a friendly reminder that you have an event coming up tomorrow!</p>
            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">{event_title}</h3>
                <p><strong>Date:</strong> {event_date}</p>
                <p><strong>Venue:</strong> {event_venue}</p>
            </div>
            {f'<p style="text-align: center;"><a href="{event_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Event Details</a></p>' if event_url else ''}
            <p>Have a great time at your event!</p>
            <p>Best regards,<br>The VoyagerAI Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Event Reminder
        
        Hi {user_name},
        
        This is a friendly reminder that you have an event coming up tomorrow!
        
        Event: {event_title}
        Date: {event_date}
        Venue: {event_venue}
        
        {f'View details: {event_url}' if event_url else ''}
        
        Have a great time at your event!
        
        Best regards,
        The VoyagerAI Team
        """
        
        return self._send_email(user_email, subject, html_content, text_content)

# Global email service instance
email_service = EmailService()
