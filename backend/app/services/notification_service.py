"""
Notification service for VoyagerAI
Handles event reminders and notifications
"""

import os
from datetime import datetime, timedelta
from .email_service import email_service
from ..models import db, Favorite, User
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.enabled = os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        
    def send_event_reminders(self):
        """Send reminders for events happening tomorrow"""
        if not self.enabled:
            logger.info("Notifications disabled, skipping event reminders")
            return
            
        try:
            # Get events happening tomorrow
            tomorrow = datetime.now().date() + timedelta(days=1)
            
            # Get all favorites for events happening tomorrow
            favorites = db.session.query(Favorite).filter(
                Favorite.date == tomorrow,
                Favorite.user_email.isnot(None)
            ).all()
            
            sent_count = 0
            for favorite in favorites:
                try:
                    # Get user info
                    user = User.query.filter_by(email=favorite.user_email).first()
                    if not user or not user.is_verified:
                        continue
                    
                    # Send reminder email
                    success = email_service.send_event_reminder_email(
                        user_email=user.email,
                        user_name=user.name,
                        event_title=favorite.title,
                        event_date=favorite.date.strftime("%B %d, %Y") if favorite.date else "TBA",
                        event_venue=favorite.venue or "TBA",
                        event_url=favorite.url
                    )
                    
                    if success:
                        sent_count += 1
                        logger.info(f"Sent reminder for {favorite.title} to {user.email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send reminder for favorite {favorite.id}: {e}")
                    continue
            
            logger.info(f"Sent {sent_count} event reminders")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending event reminders: {e}")
            return 0
    
    def send_daily_digest(self):
        """Send daily digest of upcoming events"""
        if not self.enabled:
            return
            
        try:
            # Get events happening in the next 7 days
            today = datetime.now().date()
            week_from_now = today + timedelta(days=7)
            
            # Get all verified users
            users = User.query.filter_by(is_verified=True).all()
            
            for user in users:
                try:
                    # Get user's favorites for next week
                    favorites = Favorite.query.filter(
                        Favorite.user_email == user.email,
                        Favorite.date >= today,
                        Favorite.date <= week_from_now
                    ).order_by(Favorite.date).all()
                    
                    if not favorites:
                        continue
                    
                    # Create digest content
                    events_list = []
                    for fav in favorites:
                        event_info = f"• {fav.title}"
                        if fav.date:
                            event_info += f" on {fav.date.strftime('%B %d')}"
                        if fav.venue:
                            event_info += f" at {fav.venue}"
                        events_list.append(event_info)
                    
                    # Send digest email
                    subject = f"Your VoyagerAI Weekly Digest - {len(favorites)} upcoming events"
                    
                    html_content = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #2563eb;">Your Weekly Event Digest</h2>
                        <p>Hi {user.name},</p>
                        <p>Here are your upcoming events for the next week:</p>
                        <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            {''.join([f'<p style="margin: 8px 0;">{event}</p>' for event in events_list])}
                        </div>
                        <p>Have a great week!</p>
                        <p>Best regards,<br>The VoyagerAI Team</p>
                    </body>
                    </html>
                    """
                    
                    text_content = f"""
                    Your Weekly Event Digest
                    
                    Hi {user.name},
                    
                    Here are your upcoming events for the next week:
                    
                    {chr(10).join(events_list)}
                    
                    Have a great week!
                    
                    Best regards,
                    The VoyagerAI Team
                    """
                    
                    success = email_service._send_email(
                        to_email=user.email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content
                    )
                    
                    if success:
                        logger.info(f"Sent weekly digest to {user.email}")
                    
                except Exception as e:
                    logger.error(f"Failed to send digest to {user.email}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")

# Global notification service instance
notification_service = NotificationService()
