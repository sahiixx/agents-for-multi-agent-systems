"""
Twilio SMS Integration
"""
import logging
import os
from typing import Dict, Any
from twilio.rest import Client

logger = logging.getLogger(__name__)

class TwilioIntegration:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.verify_service_sid = os.getenv("TWILIO_VERIFY_SERVICE")
        self.client = None
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
    
    async def send_otp(self, phone_number: str) -> Dict[str, Any]:
        try:
            if not self.client or not self.verify_service_sid:
                return {"error": "Twilio not configured", "test_mode": True}
            
            verification = self.client.verify.services(self.verify_service_sid).verifications.create(
                to=phone_number, 
                channel="sms"
            )
            return {"status": verification.status, "to": phone_number}
        except Exception as e:
            logger.error(f"Twilio send OTP error: {e}")
            return {"error": str(e)}
    
    async def verify_otp(self, phone_number: str, code: str) -> Dict[str, Any]:
        try:
            if not self.client or not self.verify_service_sid:
                return {"valid": code == "123456", "test_mode": True}
            
            check = self.client.verify.services(self.verify_service_sid).verification_checks.create(
                to=phone_number, 
                code=code
            )
            return {"valid": check.status == "approved", "status": check.status}
        except Exception as e:
            logger.error(f"Twilio verify OTP error: {e}")
            return {"error": str(e)}
    
    async def send_sms(self, to_number: str, message: str, from_number: str = None) -> Dict[str, Any]:
        try:
            if not self.client:
                return {"error": "Twilio not configured", "test_mode": True}
            
            from_num = from_number or os.getenv("TWILIO_PHONE_NUMBER")
            if not from_num:
                return {"error": "No Twilio phone number configured"}
            
            message_obj = self.client.messages.create(
                body=message,
                from_=from_num,
                to=to_number
            )
            return {"sid": message_obj.sid, "status": message_obj.status}
        except Exception as e:
            logger.error(f"Twilio send SMS error: {e}")
            return {"error": str(e)}

twilio_integration = TwilioIntegration()
