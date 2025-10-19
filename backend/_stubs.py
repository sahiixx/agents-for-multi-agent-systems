"""Test-time dependency stubs for optional third-party packages.

This module installs lightweight stand-ins for integrations that are not
available in the execution environment.  The goal is to provide just enough
behaviour for the unit tests to exercise the backend logic without making real
network calls or requiring heavy external dependencies.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
import types
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, Optional


_INSTALLING = False
_INSTALLED = False


def _module_available(name: str) -> bool:
    """Return ``True`` when the real module is importable."""

    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def _install_aiohttp() -> None:
    if _module_available("aiohttp"):
        return

    module = types.ModuleType("aiohttp")

    class _Response:
        def __init__(self, status: int = 200, data: Optional[Dict[str, Any]] = None) -> None:
            self.status = status
            self._data = data or {}

        async def json(self) -> Dict[str, Any]:
            return dict(self._data)

        async def text(self) -> str:
            return json.dumps(self._data)

    class _RequestContext:
        def __init__(self, response: _Response) -> None:
            self._response = response

        async def __aenter__(self) -> _Response:
            return self._response

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class ClientSession:
        """Very small async client interface used by the tests."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._default_response = _Response()

        async def __aenter__(self) -> "ClientSession":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def close(self) -> None:  # pragma: no cover - mirror real API
            return None

        def get(self, *_args: Any, **_kwargs: Any) -> _RequestContext:
            return _RequestContext(self._default_response)

        def post(self, *_args: Any, **_kwargs: Any) -> _RequestContext:
            return _RequestContext(self._default_response)

    module.ClientSession = ClientSession
    module.ClientError = Exception

    sys.modules[module.__name__] = module


def _install_psutil() -> None:
    if _module_available("psutil"):
        return

    module = types.ModuleType("psutil")

    def _meminfo() -> types.SimpleNamespace:
        return types.SimpleNamespace(total=16 * 1024**3, available=8 * 1024**3, percent=37.5)

    def _diskinfo() -> types.SimpleNamespace:
        return types.SimpleNamespace(total=256 * 1024**3, used=120 * 1024**3, free=136 * 1024**3, percent=46.9)

    def _netinfo() -> types.SimpleNamespace:
        return types.SimpleNamespace(bytes_sent=12_345_678, bytes_recv=23_456_789)

    def cpu_percent(interval: float | None = None) -> float:
        return 12.5

    module.cpu_percent = cpu_percent
    module.virtual_memory = _meminfo
    module.disk_usage = lambda _path="/": _diskinfo()
    module.net_io_counters = _netinfo

    sys.modules[module.__name__] = module


def _install_motor() -> None:
    if _module_available("motor.motor_asyncio"):
        return

    motor_pkg = types.ModuleType("motor")
    motor_asyncio = types.ModuleType("motor.motor_asyncio")

    class _AsyncCollection:
        async def create_index(self, *args: Any, **kwargs: Any) -> str:
            return "index_created"

    class _Admin:
        async def command(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
            return {"ok": 1}

    class AsyncIOMotorDatabase:
        def __init__(self) -> None:
            self._collections: Dict[str, _AsyncCollection] = {}

        def __getattr__(self, name: str) -> _AsyncCollection:
            return self._collections.setdefault(name, _AsyncCollection())

    class AsyncIOMotorClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._databases: Dict[str, AsyncIOMotorDatabase] = {}
            self.admin = _Admin()

        def __getitem__(self, name: str) -> AsyncIOMotorDatabase:
            return self._databases.setdefault(name, AsyncIOMotorDatabase())

        def close(self) -> None:  # pragma: no cover - alignment with real API
            return None

    motor_asyncio.AsyncIOMotorClient = AsyncIOMotorClient
    motor_asyncio.AsyncIOMotorDatabase = AsyncIOMotorDatabase

    motor_pkg.motor_asyncio = motor_asyncio
    sys.modules["motor"] = motor_pkg
    sys.modules["motor.motor_asyncio"] = motor_asyncio


def _install_jwt() -> None:
    if _module_available("jwt"):
        return

    module = types.ModuleType("jwt")

    class PyJWTError(Exception):
        """Base error that mirrors the real PyJWT hierarchy."""

    class InvalidTokenError(PyJWTError):
        pass

    class InvalidAlgorithmError(InvalidTokenError):
        pass

    class ExpiredSignatureError(InvalidTokenError):
        pass

    class ImmatureSignatureError(InvalidTokenError):
        pass

    class InvalidIssuedAtError(InvalidTokenError):
        pass

    class MissingRequiredClaimError(InvalidTokenError):
        pass

    class InvalidAudienceError(InvalidTokenError):
        pass

    class InvalidIssuerError(InvalidTokenError):
        pass

    exceptions_module = types.ModuleType("jwt.exceptions")
    exceptions_module.PyJWTError = PyJWTError
    exceptions_module.InvalidTokenError = InvalidTokenError
    exceptions_module.InvalidAlgorithmError = InvalidAlgorithmError
    exceptions_module.ExpiredSignatureError = ExpiredSignatureError
    exceptions_module.ImmatureSignatureError = ImmatureSignatureError
    exceptions_module.InvalidIssuedAtError = InvalidIssuedAtError
    exceptions_module.MissingRequiredClaimError = MissingRequiredClaimError
    exceptions_module.InvalidAudienceError = InvalidAudienceError
    exceptions_module.InvalidIssuerError = InvalidIssuerError

    def _normalise_datetime(value: Any) -> Any:
        """Convert ``datetime`` objects to integer timestamps."""

        if isinstance(value, datetime):
            aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return int(aware.timestamp())
        if isinstance(value, dict):
            return {k: _normalise_datetime(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_normalise_datetime(item) for item in value]
        return value

    def _coerce_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return None
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        return None

    def encode(
        payload: Dict[str, Any],
        _secret: str,
        algorithm: str = "HS256",
        headers: Optional[Dict[str, Any]] = None,
    ) -> str:  # noqa: ARG001 - signature parity
        prepared = _normalise_datetime(payload)
        data = json.dumps({"payload": prepared, "alg": algorithm, "headers": headers or {}}, default=str)
        return base64.urlsafe_b64encode(data.encode()).decode()

    def decode(
        token: str,
        _secret: str | None = None,
        algorithms: Iterable[str] | str | None = None,
        options: Optional[Dict[str, Any]] = None,
        audience: Any | None = None,
        issuer: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            data = json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive branch
            raise InvalidTokenError("Invalid token") from exc

        algorithm = data.get("alg")

        if algorithms is not None:
            if isinstance(algorithms, str):
                allowed = {algorithms}
            else:
                allowed = set(algorithms)
            if algorithm not in allowed:
                raise InvalidAlgorithmError("Algorithm not supported")

        payload = dict(data.get("payload", {}))

        opts = {
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
        }
        required_claims: set[str] = set()
        if options:
            require_option = options.get("require")
            if require_option is not None:
                if isinstance(require_option, str):
                    required_claims = {require_option}
                else:
                    required_claims = set(require_option)
            opts.update({k: v for k, v in options.items() if k != "require"})

        if required_claims:
            missing = [claim for claim in required_claims if claim not in payload]
            if missing:
                raise MissingRequiredClaimError(
                    "Missing required claim(s): " + ", ".join(sorted(missing))
                )

        if audience is None and "audience" in kwargs:
            audience = kwargs["audience"]
        if issuer is None and "issuer" in kwargs:
            issuer = kwargs["issuer"]

        leeway_value = kwargs.get("leeway", 0)
        if isinstance(leeway_value, timedelta):
            leeway_delta = leeway_value
        else:
            try:
                seconds = float(leeway_value)
            except (TypeError, ValueError):  # pragma: no cover - defensive guard
                seconds = 0.0
            leeway_delta = timedelta(seconds=seconds)

        if opts.get("verify_exp", True):
            exp_value = payload.get("exp")
            exp = _coerce_datetime(exp_value)
            if exp is not None:
                now = datetime.now(timezone.utc)
                if exp + leeway_delta < now:
                    raise ExpiredSignatureError("Signature has expired")

        if opts.get("verify_nbf", True):
            nbf_value = payload.get("nbf")
            nbf = _coerce_datetime(nbf_value)
            if nbf is not None:
                now = datetime.now(timezone.utc)
                if now + leeway_delta < nbf:
                    raise ImmatureSignatureError("Token is not yet valid")

        if opts.get("verify_iat", True):
            iat_value = payload.get("iat")
            iat = _coerce_datetime(iat_value)
            if iat is not None:
                now = datetime.now(timezone.utc)
                if iat - leeway_delta > now:
                    raise InvalidIssuedAtError("Issued At claim (iat) is in the future")

        if opts.get("verify_aud", True) and audience is not None:
            aud_claim = payload.get("aud")
            if aud_claim is None:
                raise MissingRequiredClaimError("Missing required claim(s): aud")
            if isinstance(audience, str):
                expected_audiences = {audience}
            else:
                expected_audiences = set(audience)
            if isinstance(aud_claim, str):
                aud_values = {aud_claim}
            elif isinstance(aud_claim, (list, tuple, set)):
                aud_values = set(aud_claim)
            else:
                aud_values = {aud_claim}
            if not aud_values & expected_audiences:
                raise InvalidAudienceError("Invalid audience")

        if opts.get("verify_iss", True) and issuer is not None:
            iss_claim = payload.get("iss")
            if iss_claim != issuer:
                raise InvalidIssuerError("Invalid issuer")

        return payload

    module.encode = encode
    module.decode = decode
    module.PyJWTError = PyJWTError
    module.InvalidTokenError = InvalidTokenError
    module.InvalidAlgorithmError = InvalidAlgorithmError
    module.ExpiredSignatureError = ExpiredSignatureError
    module.ImmatureSignatureError = ImmatureSignatureError
    module.InvalidIssuedAtError = InvalidIssuedAtError
    module.MissingRequiredClaimError = MissingRequiredClaimError
    module.InvalidAudienceError = InvalidAudienceError
    module.InvalidIssuerError = InvalidIssuerError
    module.exceptions = exceptions_module

    sys.modules[module.__name__] = module
    sys.modules[exceptions_module.__name__] = exceptions_module


def _install_numpy() -> None:
    if _module_available("numpy"):
        return

    module = types.ModuleType("numpy")

    def corrcoef(*_args: Any, **_kwargs: Any) -> list[list[float]]:
        return [[1.0, 0.0], [0.0, 1.0]]

    module.corrcoef = corrcoef

    sys.modules[module.__name__] = module


def _install_pydantic() -> None:
    if _module_available("pydantic"):
        return

    module = types.ModuleType("pydantic")

    @dataclass
    class _FieldInfo:
        default: Any = None
        default_factory: Optional[Any] = None
        metadata: Dict[str, Any] | None = None

    def Field(default: Any = None, *, default_factory: Optional[Any] = None, **metadata: Any) -> _FieldInfo:
        return _FieldInfo(default=default, default_factory=default_factory, metadata=metadata or {})

    class _BaseModelMeta(type):
        def __new__(mcls, name: str, bases: tuple[type, ...], namespace: Dict[str, Any]):
            field_defaults: Dict[str, _FieldInfo] = {}
            for attr, value in namespace.items():
                if isinstance(value, _FieldInfo):
                    field_defaults[attr] = value
            cls = super().__new__(mcls, name, bases, namespace)
            combined: Dict[str, _FieldInfo] = {}
            for base in reversed(cls.__mro__[1:]):
                combined.update(getattr(base, "__field_defaults__", {}))
            combined.update(field_defaults)
            cls.__field_defaults__ = combined
            return cls

    class BaseModel(metaclass=_BaseModelMeta):
        __field_defaults__: Dict[str, _FieldInfo]

        def __init__(self, **data: Any) -> None:
            for name, info in self.__class__.__field_defaults__.items():
                if name not in data:
                    if info.default_factory is not None:
                        value = info.default_factory()
                    else:
                        value = info.default
                    setattr(self, name, value)
            for name, value in data.items():
                setattr(self, name, value)

        def dict(self) -> Dict[str, Any]:
            return dict(self.__dict__)

        def model_dump(self) -> Dict[str, Any]:  # pragma: no cover - alias
            return self.dict()

    module.BaseModel = BaseModel
    module.Field = Field
    module.EmailStr = str

    sys.modules[module.__name__] = module


def _install_pydantic_settings() -> None:
    if _module_available("pydantic_settings"):
        return

    module = types.ModuleType("pydantic_settings")

    class BaseSettings:
        def __init__(self, **values: Any) -> None:
            for name, value in values.items():
                setattr(self, name, value)

    module.BaseSettings = BaseSettings
    sys.modules[module.__name__] = module


def _install_sendgrid() -> None:
    if _module_available("sendgrid"):
        return

    sendgrid_module = types.ModuleType("sendgrid")
    helpers_module = types.ModuleType("sendgrid.helpers")
    mail_module = types.ModuleType("sendgrid.helpers.mail")

    class _SendGridResponse:
        def __init__(self, status_code: int = 202) -> None:
            self.status_code = status_code

    class SendGridAPIClient:
        def __init__(self, api_key: str | None = None) -> None:
            self.api_key = api_key

        def send(self, _message: Any) -> _SendGridResponse:
            return _SendGridResponse()

    class Mail:
        def __init__(self, from_email: str | None = None, to_emails: Any | None = None, subject: str | None = None,
                     html_content: str | None = None, plain_text_content: str | None = None) -> None:
            self.from_email = from_email
            self.to_emails = to_emails
            self.subject = subject
            self.html_content = html_content
            self.plain_text_content = plain_text_content
            self.template_id: Optional[str] = None
            self.dynamic_template_data: Optional[Dict[str, Any]] = None

    sendgrid_module.SendGridAPIClient = SendGridAPIClient
    mail_module.Mail = Mail
    helpers_module.mail = mail_module
    sendgrid_module.helpers = helpers_module

    sys.modules["sendgrid"] = sendgrid_module
    sys.modules["sendgrid.helpers"] = helpers_module
    sys.modules["sendgrid.helpers.mail"] = mail_module


def _install_twilio() -> None:
    if _module_available("twilio.rest"):
        return

    twilio_module = types.ModuleType("twilio")
    rest_module = types.ModuleType("twilio.rest")

    class _Verifications:
        def create(self, *args: Any, **kwargs: Any) -> types.SimpleNamespace:
            return types.SimpleNamespace(status="pending")

    class _VerificationChecks:
        def create(self, *args: Any, **kwargs: Any) -> types.SimpleNamespace:
            code = kwargs.get("code")
            status = "approved" if code == "123456" else "pending"
            return types.SimpleNamespace(status=status)

    class _VerifyService:
        def services(self, _sid: str) -> "_VerifyService":
            return self

        @property
        def verifications(self) -> _Verifications:
            return _Verifications()

        @property
        def verification_checks(self) -> _VerificationChecks:
            return _VerificationChecks()

    class _Messages:
        def create(self, *args: Any, **kwargs: Any) -> types.SimpleNamespace:
            return types.SimpleNamespace(sid=str(uuid.uuid4()), status="sent")

    class Client:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.verify = _VerifyService()
            self.messages = _Messages()

    rest_module.Client = Client
    twilio_module.rest = rest_module

    sys.modules["twilio"] = twilio_module
    sys.modules["twilio.rest"] = rest_module


def _install_emergent_llm() -> None:
    if _module_available("emergentintegrations.llm.chat"):
        return

    root_pkg = sys.modules.setdefault("emergentintegrations", types.ModuleType("emergentintegrations"))
    llm_pkg = getattr(root_pkg, "llm", types.ModuleType("emergentintegrations.llm"))
    chat_module = types.ModuleType("emergentintegrations.llm.chat")
    openai_module = types.ModuleType("emergentintegrations.llm.openai")

    @dataclass
    class ImageContent:
        image_base64: str | None = None

    @dataclass
    class FileContentWithMimeType:
        file_path: str
        mime_type: str

    @dataclass
    class UserMessage:
        text: str
        file_contents: Iterable[Any] | None = None

    class LlmChat:
        def __init__(self, api_key: str, session_id: str, system_message: Optional[str] = None) -> None:
            self.api_key = api_key
            self.session_id = session_id
            self.system_message = system_message
            self.model = ("openai", "gpt-4o")
            self.max_tokens = 2048

        def with_model(self, provider: str, model: str) -> "LlmChat":
            self.model = (provider, model)
            return self

        def with_max_tokens(self, max_tokens: int) -> "LlmChat":
            self.max_tokens = max_tokens
            return self

        async def send_message(self, message: UserMessage) -> str:
            prompt = message.text or ""
            timestamp = datetime.utcnow().isoformat()
            return f"Simulated response for '{prompt}' at {timestamp}"

    class OpenAIChatRealtime:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

    chat_module.LlmChat = LlmChat
    chat_module.UserMessage = UserMessage
    chat_module.ImageContent = ImageContent
    chat_module.FileContentWithMimeType = FileContentWithMimeType
    openai_module.OpenAIChatRealtime = OpenAIChatRealtime

    setattr(root_pkg, "llm", llm_pkg)
    setattr(llm_pkg, "chat", chat_module)
    setattr(llm_pkg, "openai", openai_module)

    sys.modules["emergentintegrations.llm"] = llm_pkg
    sys.modules["emergentintegrations.llm.chat"] = chat_module
    sys.modules["emergentintegrations.llm.openai"] = openai_module


def _install_emergent_payments() -> None:
    if _module_available("emergentintegrations.payments.stripe.checkout"):
        return

    root_pkg = sys.modules.setdefault("emergentintegrations", types.ModuleType("emergentintegrations"))
    payments_pkg = types.ModuleType("emergentintegrations.payments")
    stripe_pkg = types.ModuleType("emergentintegrations.payments.stripe")
    checkout_module = types.ModuleType("emergentintegrations.payments.stripe.checkout")

    @dataclass
    class CheckoutSessionRequest:
        amount: float
        currency: str
        success_url: str
        cancel_url: str
        metadata: Dict[str, Any]

    @dataclass
    class CheckoutSessionResponse:
        url: str
        session_id: str

    @dataclass
    class CheckoutStatusResponse:
        status: str
        payment_status: str
        amount_total: float
        currency: str

    class StripeCheckout:
        def __init__(self, api_key: str, webhook_url: str) -> None:
            self.api_key = api_key
            self.webhook_url = webhook_url

        async def create_checkout_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
            session = str(uuid.uuid4())
            return CheckoutSessionResponse(url=f"https://checkout.stripe.test/session/{session}", session_id=session)

        async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
            return CheckoutStatusResponse(status="complete", payment_status="paid", amount_total=0.0, currency="aed")

    checkout_module.CheckoutSessionRequest = CheckoutSessionRequest
    checkout_module.CheckoutSessionResponse = CheckoutSessionResponse
    checkout_module.CheckoutStatusResponse = CheckoutStatusResponse
    checkout_module.StripeCheckout = StripeCheckout

    root_pkg.payments = payments_pkg
    payments_pkg.stripe = stripe_pkg
    stripe_pkg.checkout = checkout_module

    sys.modules["emergentintegrations.payments"] = payments_pkg
    sys.modules["emergentintegrations.payments.stripe"] = stripe_pkg
    sys.modules["emergentintegrations.payments.stripe.checkout"] = checkout_module


def install() -> None:
    """Install all stub modules required for the test environment."""

    global _INSTALLING, _INSTALLED

    if _INSTALLED or _INSTALLING:
        return

    _INSTALLING = True
    try:
        _install_aiohttp()
        _install_psutil()
        _install_motor()
        _install_jwt()
        _install_numpy()
        _install_pydantic()
        _install_pydantic_settings()
        _install_sendgrid()
        _install_twilio()
        _install_emergent_llm()
        _install_emergent_payments()
        _INSTALLED = True
    finally:
        _INSTALLING = False

