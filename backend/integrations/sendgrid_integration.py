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
        """
        Initializes the SendGridIntegration by reading configuration from environment variables and creating a SendGrid client when an API key is present.
        
        Reads SENDGRID_API_KEY and SENDGRID_FROM_EMAIL (defaults to "noreply@nowheredigital.ae"), stores them on the instance, and instantiates a SendGridAPIClient assigned to `client` only if an API key was provided.
        
        Attributes:
            api_key (Optional[str]): The SendGrid API key from the environment or None if not set.
            from_email (str): The sender email address from the environment or the default.
            client (Optional[SendGridAPIClient]): Initialized SendGrid client when `api_key` is present, otherwise None.
        """
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
        """
        Send an email with HTML content and an optional plain-text fallback.
        
        If the SendGrid client is not configured, returns {"error": "SendGrid not configured", "test_mode": True}. On success returns {"status_code": int, "success": True} when the SendGrid API accepts the message; otherwise "success" is False. On exception returns {"error": "<error message>"}.
        
        Parameters:
            to_email (str): Recipient email address.
            subject (str): Email subject line.
            html_content (str): HTML body of the email.
            plain_text (Optional[str]): Optional plain-text body for clients that do not render HTML.
        
        Returns:
            dict: Result object containing either:
                - {"status_code": int, "success": bool} on send attempt, or
                - {"error": str} (and possibly "test_mode": True) when configuration is missing or an error occurs.
        """
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
        """
        Send an email using a SendGrid dynamic template to a recipient.
        
        Parameters:
            to_email (str): Recipient email address.
            template_id (str): SendGrid dynamic template ID to use for the message.
            dynamic_data (Dict[str, Any]): Mapping of template placeholder names to values for dynamic replacement.
        
        Returns:
            Dict[str, Any]: On success, returns {"status_code": int, "success": True} when SendGrid responds with status 202, or {"status_code": int, "success": False} for other responses. If the SendGrid client is not configured, returns {"error": "SendGrid not configured", "test_mode": True}. On exception, returns {"error": str(exception)}.
        """
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
        """
        Send a notification email built from a notification type and associated data.
        
        Parameters:
            to_email (str): Recipient email address.
            notification_type (str): Type of notification; controls the subject. Common values: "welcome", "alert", "report".
            data (Dict[str, Any]): Content for the message. Expected keys:
                - "message" (str, optional): Main message text; defaults to "You have a new notification.".
                - "details" (str, optional): Additional HTML content to include in the body.
        
        Returns:
            Dict[str, Any]: Result dictionary. On success contains `status_code` (int) and `success` (bool).
            If SendGrid is not configured returns `{"error": "SendGrid not configured", "test_mode": True}`.
            On failure returns `{"error": "<error message>"}`.
        """
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