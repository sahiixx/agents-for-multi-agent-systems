"""
SendGrid Email Integration
"""
import logging
import os
from typing import Dict, Any, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class SendGridIntegration:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@nowheredigital.ae")
        self.client = None
        
        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        plain_text: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if not self.client:
                return {"error": "SendGrid not configured", "test_mode": True}
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text
            )
            
            response = self.client.send(message)
            return {"status_code": response.status_code, "success": response.status_code == 202}
        except Exception as e:
            logger.error(f"SendGrid send email error: {e}")
            return {"error": str(e)}
    
    async def send_template_email(
        self,
        to_email: str,
        template_id: str,
        dynamic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            if not self.client:
                return {"error": "SendGrid not configured", "test_mode": True}
            
            message = Mail(from_email=self.from_email, to_emails=to_email)
            message.template_id = template_id
            message.dynamic_template_data = dynamic_data
            
            response = self.client.send(message)
            return {"status_code": response.status_code, "success": response.status_code == 202}
        except Exception as e:
            logger.error(f"SendGrid template email error: {e}")
            return {"error": str(e)}
    
    async def send_notification(
        self,
        to_email: str,
        notification_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send notification emails (welcome, alert, etc.)"""
        subjects = {
            "welcome": "Welcome to NOWHERE Digital Platform",
            "alert": "System Alert Notification",
            "report": "Your Performance Report is Ready"
        }
        
        subject = subjects.get(notification_type, "Notification from NOWHERE Digital")
        
        html_content = f"""
        <html>
            <body>
                <h2>{subject}</h2>
                <p>{data.get('message', 'You have a new notification.')}</p>
                <div style="margin: 20px 0;">
                    {data.get('details', '')}
                </div>
                <p>Best regards,<br>NOWHERE Digital Team</p>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, html_content)

sendgrid_integration = SendGridIntegration()
