"""
Unit tests for backend/_stubs.py
Tests stub module installation and behavior for test environment
"""
import pytest
import sys
import types
import os
from unittest.mock import patch, MagicMock
from backend._stubs import (
    _module_available,
    _install_aiohttp,
    _install_psutil,
    _install_motor,
    _install_jwt,
    _install_numpy,
    _install_pydantic,
    _install_pydantic_settings,
    _install_sendgrid,
    _install_twilio,
    _install_emergent_llm,
    _install_emergent_payments,
    install
)

# Test JWT secret - can be overridden via environment variable
TEST_JWT_SECRET = os.getenv("JWT_TEST_SECRET", "test-secret-key")


class TestModuleAvailable:
    """Test module availability checking"""
    
    def test_module_available_for_existing_module(self):
        """Test that existing modules are detected"""
        assert _module_available("sys") is True
        assert _module_available("os") is True
    
    def test_module_available_for_nonexistent_module(self):
        """Test that non-existent modules return False"""
        assert _module_available("nonexistent_module_xyz") is False
    
    def test_module_available_for_already_imported(self):
        """Test detection of already imported modules"""
        import json
        assert _module_available("json") is True


class TestAiohttpStub:
    """Test aiohttp stub installation"""
    
    def test_install_aiohttp_creates_module(self):
        """Test that aiohttp stub creates module in sys.modules"""
        # Remove if exists
        if 'aiohttp' in sys.modules:
            del sys.modules['aiohttp']
        
        _install_aiohttp()
        
        assert 'aiohttp' in sys.modules
        assert hasattr(sys.modules['aiohttp'], 'ClientSession')
        assert hasattr(sys.modules['aiohttp'], 'ClientError')
    
    @pytest.mark.asyncio
    async def test_aiohttp_client_session_basic(self):
        """Test basic ClientSession functionality"""
        _install_aiohttp()
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get("http://test.com") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_aiohttp_client_session_post(self):
        """Test POST request handling"""
        _install_aiohttp()
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://test.com", json={"key": "value"}) as resp:
                assert resp.status == 200
                text = await resp.text()
                assert isinstance(text, str)


class TestPsutilStub:
    """Test psutil stub installation"""
    
    def test_install_psutil_creates_module(self):
        """Test that psutil stub creates module"""
        if 'psutil' in sys.modules:
            del sys.modules['psutil']
        
        _install_psutil()
        
        assert 'psutil' in sys.modules
        assert hasattr(sys.modules['psutil'], 'cpu_percent')
        assert hasattr(sys.modules['psutil'], 'virtual_memory')
        assert hasattr(sys.modules['psutil'], 'disk_usage')
        assert hasattr(sys.modules['psutil'], 'net_io_counters')
    
    def test_psutil_cpu_percent(self):
        """Test CPU percentage stub"""
        _install_psutil()
        import psutil
        
        cpu = psutil.cpu_percent()
        assert isinstance(cpu, float)
        assert 0 <= cpu <= 100
    
    def test_psutil_virtual_memory(self):
        """Test virtual memory stub"""
        _install_psutil()
        import psutil
        
        mem = psutil.virtual_memory()
        assert hasattr(mem, 'total')
        assert hasattr(mem, 'available')
        assert hasattr(mem, 'percent')
        assert mem.total > 0
    
    def test_psutil_disk_usage(self):
        """Test disk usage stub"""
        _install_psutil()
        import psutil
        
        disk = psutil.disk_usage("/")
        assert hasattr(disk, 'total')
        assert hasattr(disk, 'used')
        assert hasattr(disk, 'free')
        assert hasattr(disk, 'percent')
    
    def test_psutil_net_io_counters(self):
        """Test network I/O counters stub"""
        _install_psutil()
        import psutil
        
        net = psutil.net_io_counters()
        assert hasattr(net, 'bytes_sent')
        assert hasattr(net, 'bytes_recv')


class TestMotorStub:
    """Test motor stub installation"""
    
    def test_install_motor_creates_modules(self):
        """Test that motor stub creates necessary modules"""
        if 'motor' in sys.modules:
            del sys.modules['motor']
        if 'motor.motor_asyncio' in sys.modules:
            del sys.modules['motor.motor_asyncio']
        
        _install_motor()
        
        assert 'motor' in sys.modules
        assert 'motor.motor_asyncio' in sys.modules
        
        motor_asyncio = sys.modules['motor.motor_asyncio']
        assert hasattr(motor_asyncio, 'AsyncIOMotorClient')
        assert hasattr(motor_asyncio, 'AsyncIOMotorDatabase')
    
    @pytest.mark.asyncio
    async def test_motor_client_creation(self):
        """Test motor client creation"""
        _install_motor()
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        assert client is not None
        
        db = client["test_db"]
        assert db is not None
    
    @pytest.mark.asyncio
    async def test_motor_collection_operations(self):
        """Test motor collection operations"""
        _install_motor()
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        db = client["test_db"]
        collection = db.test_collection
        
        # Test index creation
        result = await collection.create_index("test_field")
        assert result == "index_created"
    
    @pytest.mark.asyncio
    async def test_motor_admin_commands(self):
        """Test motor admin commands"""
        _install_motor()
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        result = await client.admin.command("ping")
        
        assert result == {"ok": 1}


class TestJWTStub:
    """Test JWT stub installation"""
    
    def test_install_jwt_creates_modules(self):
        """Test that JWT stub creates modules"""
        if 'jwt' in sys.modules:
            del sys.modules['jwt']
        
        _install_jwt()
        
        assert 'jwt' in sys.modules
        assert hasattr(sys.modules['jwt'], 'encode')
        assert hasattr(sys.modules['jwt'], 'decode')
        assert 'jwt.exceptions' in sys.modules
    
    def test_jwt_encode_basic(self):
        """Test basic JWT encoding"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123", "role": "admin"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_decode_basic(self):
        """Test basic JWT decoding"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123", "role": "admin"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        decoded = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
        
        assert decoded["user_id"] == "123"
        assert decoded["role"] == "admin"
    
    def test_jwt_decode_with_expiration(self):
        """Test JWT decoding with expiration"""
        _install_jwt()
        import jwt
        from datetime import datetime, timezone, timedelta
        
        # Create expired token
        payload = {
            "user_id": "123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"])
    
    def test_jwt_decode_with_invalid_algorithm(self):
        """Test JWT decoding with invalid algorithm"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        # Try to decode with different algorithm
        with pytest.raises(jwt.InvalidAlgorithmError):
            jwt.decode(token, TEST_JWT_SECRET, algorithms=["RS256"])
    
    def test_jwt_decode_with_audience(self):
        """Test JWT decoding with audience validation"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123", "aud": "test-audience"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        # Should work with correct audience
        decoded = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], audience="test-audience")
        assert decoded["aud"] == "test-audience"
        
        # Should fail with wrong audience
        with pytest.raises(jwt.InvalidAudienceError):
            jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], audience="wrong-audience")
    
    def test_jwt_decode_with_issuer(self):
        """Test JWT decoding with issuer validation"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123", "iss": "test-issuer"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        # Should work with correct issuer
        decoded = jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], issuer="test-issuer")
        assert decoded["iss"] == "test-issuer"
        
        # Should fail with wrong issuer
        with pytest.raises(jwt.InvalidIssuerError):
            jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], issuer="wrong-issuer")
    
    def test_jwt_required_claims(self):
        """Test JWT with required claims"""
        _install_jwt()
        import jwt
        
        payload = {"user_id": "123", "role": "admin"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        
        # Should work with present claims
        decoded = jwt.decode(
            token, TEST_JWT_SECRET, 
            algorithms=["HS256"],
            options={"require": ["user_id", "role"]}
        )
        assert decoded["user_id"] == "123"
        
        # Should fail with missing required claim
        with pytest.raises(jwt.MissingRequiredClaimError):
            jwt.decode(
                token, TEST_JWT_SECRET,
                algorithms=["HS256"],
                options={"require": ["user_id", "role", "missing_claim"]}
            )


class TestNumpyStub:
    """Test numpy stub installation"""
    
    def test_install_numpy_creates_module(self):
        """Test that numpy stub creates module"""
        if 'numpy' in sys.modules:
            del sys.modules['numpy']
        
        _install_numpy()
        
        assert 'numpy' in sys.modules
        assert hasattr(sys.modules['numpy'], 'corrcoef')
    
    def test_numpy_corrcoef(self):
        """Test numpy correlation coefficient stub"""
        _install_numpy()
        import numpy as np
        
        result = np.corrcoef([1, 2, 3], [4, 5, 6])
        assert isinstance(result, list)
        assert len(result) == 2
        assert len(result[0]) == 2


class TestPydanticStub:
    """Test pydantic stub installation"""
    
    def test_install_pydantic_creates_module(self):
        """Test that pydantic stub creates module"""
        if 'pydantic' in sys.modules:
            del sys.modules['pydantic']
        
        _install_pydantic()
        
        assert 'pydantic' in sys.modules
        assert hasattr(sys.modules['pydantic'], 'BaseModel')
        assert hasattr(sys.modules['pydantic'], 'Field')
    
    def test_pydantic_base_model(self):
        """Test pydantic BaseModel stub"""
        _install_pydantic()
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str
            age: int = Field(default=25)
        
        model = TestModel(name="John")
        assert model.name == "John"
        assert model.age == 25
    
    def test_pydantic_model_dict(self):
        """Test pydantic model dict conversion"""
        _install_pydantic()
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        model = TestModel(name="test", value=42)
        data = model.dict()
        
        assert isinstance(data, dict)
        assert data["name"] == "test"
        assert data["value"] == 42


class TestSendGridStub:
    """Test SendGrid stub installation"""
    
    def test_install_sendgrid_creates_modules(self):
        """Test that SendGrid stub creates modules"""
        if 'sendgrid' in sys.modules:
            del sys.modules['sendgrid']
        
        _install_sendgrid()
        
        assert 'sendgrid' in sys.modules
        assert 'sendgrid.helpers.mail' in sys.modules
        
        sendgrid = sys.modules['sendgrid']
        assert hasattr(sendgrid, 'SendGridAPIClient')
    
    def test_sendgrid_client_creation(self):
        """Test SendGrid client creation"""
        _install_sendgrid()
        from sendgrid import SendGridAPIClient
        
        client = SendGridAPIClient(api_key="test_key")
        assert client.api_key == "test_key"
    
    def test_sendgrid_mail_creation(self):
        """Test SendGrid Mail creation"""
        _install_sendgrid()
        from sendgrid.helpers.mail import Mail
        
        mail = Mail(
            from_email="sender@test.com",
            to_emails="recipient@test.com",
            subject="Test Subject",
            html_content="<p>Test content</p>"
        )
        
        assert mail.from_email == "sender@test.com"
        assert mail.to_emails == "recipient@test.com"
        assert mail.subject == "Test Subject"
    
    def test_sendgrid_send_mail(self):
        """Test SendGrid mail sending"""
        _install_sendgrid()
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        client = SendGridAPIClient(api_key="test_key")
        mail = Mail(
            from_email="sender@test.com",
            to_emails="recipient@test.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        response = client.send(mail)
        assert response.status_code == 202


class TestTwilioStub:
    """Test Twilio stub installation"""
    
    def test_install_twilio_creates_modules(self):
        """Test that Twilio stub creates modules"""
        if 'twilio' in sys.modules:
            del sys.modules['twilio']
        
        _install_twilio()
        
        assert 'twilio' in sys.modules
        assert 'twilio.rest' in sys.modules
        
        rest = sys.modules['twilio.rest']
        assert hasattr(rest, 'Client')
    
    def test_twilio_client_creation(self):
        """Test Twilio client creation"""
        _install_twilio()
        from twilio.rest import Client
        
        client = Client("test_sid", "test_token")
        assert client is not None
        assert hasattr(client, 'verify')
        assert hasattr(client, 'messages')
    
    def test_twilio_verify_send(self):
        """Test Twilio verify send"""
        _install_twilio()
        from twilio.rest import Client
        
        client = Client("test_sid", "test_token")
        verification = client.verify.services("test_service").verifications.create(
            to="+1234567890",
            channel="sms"
        )
        
        assert verification.status == "pending"
    
    def test_twilio_verify_check(self):
        """Test Twilio verify check"""
        _install_twilio()
        from twilio.rest import Client
        
        client = Client("test_sid", "test_token")
        
        # Correct code
        check = client.verify.services("test_service").verification_checks.create(
            to="+1234567890",
            code="123456"
        )
        assert check.status == "approved"
        
        # Wrong code
        check = client.verify.services("test_service").verification_checks.create(
            to="+1234567890",
            code="000000"
        )
        assert check.status == "pending"
    
    def test_twilio_messages_create(self):
        """Test Twilio message creation"""
        _install_twilio()
        from twilio.rest import Client
        
        client = Client("test_sid", "test_token")
        message = client.messages.create(
            to="+1234567890",
            from_="+0987654321",
            body="Test message"
        )
        
        assert message.status == "sent"
        assert hasattr(message, 'sid')


class TestEmergentLLMStub:
    """Test Emergent LLM stub installation"""
    
    def test_install_emergent_llm_creates_modules(self):
        """Test that Emergent LLM stub creates modules"""
        if 'emergentintegrations' in sys.modules:
            del sys.modules['emergentintegrations']
        
        _install_emergent_llm()
        
        assert 'emergentintegrations.llm.chat' in sys.modules
        
        chat_module = sys.modules['emergentintegrations.llm.chat']
        assert hasattr(chat_module, 'LlmChat')
        assert hasattr(chat_module, 'UserMessage')
        assert hasattr(chat_module, 'ImageContent')
    
    @pytest.mark.asyncio
    async def test_emergent_llm_chat_creation(self):
        """Test LlmChat creation"""
        _install_emergent_llm()
        from emergentintegrations.llm.chat import LlmChat
        
        chat = LlmChat(
            api_key="test_key",
            session_id="test_session",
            system_message="You are a helpful assistant"
        )
        
        assert chat.api_key == "test_key"
        assert chat.session_id == "test_session"
        assert chat.system_message == "You are a helpful assistant"
    
    @pytest.mark.asyncio
    async def test_emergent_llm_send_message(self):
        """Test sending message via LlmChat"""
        _install_emergent_llm()
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key="test_key",
            session_id="test_session"
        )
        
        message = UserMessage(text="Hello, how are you?")
        response = await chat.send_message(message)
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_emergent_llm_with_model(self):
        """Test LlmChat model configuration"""
        _install_emergent_llm()
        from emergentintegrations.llm.chat import LlmChat
        
        chat = LlmChat(api_key="test_key", session_id="test_session")
        chat.with_model("openai", "gpt-4o")
        
        assert chat.model == ("openai", "gpt-4o")
    
    @pytest.mark.asyncio
    async def test_emergent_llm_with_max_tokens(self):
        """Test LlmChat max tokens configuration"""
        _install_emergent_llm()
        from emergentintegrations.llm.chat import LlmChat
        
        chat = LlmChat(api_key="test_key", session_id="test_session")
        chat.with_max_tokens(4096)
        
        assert chat.max_tokens == 4096


class TestEmergentPaymentsStub:
    """Test Emergent Payments stub installation"""
    
    def test_install_emergent_payments_creates_modules(self):
        """Test that Emergent Payments stub creates modules"""
        if 'emergentintegrations' in sys.modules:
            # Keep emergentintegrations but remove payments
            pass
        
        _install_emergent_payments()
        
        assert 'emergentintegrations.payments.stripe.checkout' in sys.modules
        
        checkout_module = sys.modules['emergentintegrations.payments.stripe.checkout']
        assert hasattr(checkout_module, 'StripeCheckout')
        assert hasattr(checkout_module, 'CheckoutSessionRequest')
        assert hasattr(checkout_module, 'CheckoutSessionResponse')
    
    @pytest.mark.asyncio
    async def test_stripe_checkout_creation(self):
        """Test StripeCheckout creation"""
        _install_emergent_payments()
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        checkout = StripeCheckout(
            api_key="test_key",
            webhook_url="https://example.com/webhook"
        )
        
        assert checkout.api_key == "test_key"
        assert checkout.webhook_url == "https://example.com/webhook"
    
    @pytest.mark.asyncio
    async def test_stripe_create_checkout_session(self):
        """Test creating checkout session"""
        _install_emergent_payments()
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout,
            CheckoutSessionRequest
        )
        
        checkout = StripeCheckout(api_key="test_key", webhook_url="https://example.com/webhook")
        request = CheckoutSessionRequest(
            amount=100.0,
            currency="AED",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            metadata={"order_id": "123"}
        )
        
        response = await checkout.create_checkout_session(request)
        
        assert hasattr(response, 'url')
        assert hasattr(response, 'session_id')
        assert isinstance(response.url, str)
        assert isinstance(response.session_id, str)
    
    @pytest.mark.asyncio
    async def test_stripe_get_checkout_status(self):
        """Test getting checkout status"""
        _install_emergent_payments()
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        checkout = StripeCheckout(api_key="test_key", webhook_url="https://example.com/webhook")
        status = await checkout.get_checkout_status("test_session_id")
        
        assert hasattr(status, 'status')
        assert hasattr(status, 'payment_status')
        assert hasattr(status, 'amount_total')
        assert hasattr(status, 'currency')


class TestInstallFunction:
    """Test main install function"""
    
    def test_install_all_stubs(self):
        """Test that install() installs all stubs"""
        # Clean up
        modules_to_remove = [
            'aiohttp', 'psutil', 'motor', 'motor.motor_asyncio',
            'jwt', 'jwt.exceptions', 'numpy', 'pydantic', 'pydantic_settings',
            'sendgrid', 'sendgrid.helpers', 'sendgrid.helpers.mail',
            'twilio', 'twilio.rest'
        ]
        
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        
        # Install all
        install()
        
        # Verify key modules are present
        assert 'aiohttp' in sys.modules
        assert 'psutil' in sys.modules
        assert 'motor.motor_asyncio' in sys.modules
        assert 'jwt' in sys.modules
        assert 'numpy' in sys.modules
        assert 'pydantic' in sys.modules
        assert 'sendgrid' in sys.modules
        assert 'twilio.rest' in sys.modules
    
    def test_install_idempotent(self):
        """Test that install() can be called multiple times safely"""
        install()
        install()
        install()
        
        # Should still work
        assert 'aiohttp' in sys.modules
        assert 'jwt' in sys.modules