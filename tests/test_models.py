"""
Unit tests for backend/models.py
Tests data models, enums, and validation
"""
import pytest
from datetime import datetime, date
from pydantic import ValidationError
from backend.models import (
    # Enums
    ContactStatus,
    ServiceType,
    ProjectStatus,
    BookingStatus,
    UserRole,
    # Base Models
    BaseDocument,
    # Contact Forms
    ContactForm,
    ContactFormCreate,
    ContactFormUpdate,
    # User Models
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    # Portfolio Models
    Portfolio,
    PortfolioCreate,
    PortfolioUpdate,
    # Booking Models
    Booking,
    BookingCreate,
    BookingUpdate,
    # Chat Models
    ChatMessage,
    ChatMessageCreate,
    ChatSession,
    # Content Generation
    ContentGeneration,
    ContentGenerationCreate,
    # Service Models
    Service,
    ServiceCreate,
    ServiceUpdate,
    # Testimonial Models
    Testimonial,
    TestimonialCreate,
    TestimonialUpdate,
    # Analytics Models
    Analytics,
    # Email Template
    EmailTemplate,
    # Response Models
    StandardResponse,
    PaginatedResponse
)


class TestEnums:
    """Test enum definitions"""
    
    def test_contact_status_enum(self):
        """Test ContactStatus enum values"""
        assert ContactStatus.NEW.value == "new"
        assert ContactStatus.CONTACTED.value == "contacted"
        assert ContactStatus.QUALIFIED.value == "qualified"
        assert ContactStatus.CONVERTED.value == "converted"
        assert ContactStatus.CLOSED.value == "closed"
    
    def test_service_type_enum(self):
        """Test ServiceType enum values"""
        assert ServiceType.SOCIAL_MEDIA.value == "social_media"
        assert ServiceType.WHATSAPP.value == "whatsapp"
        assert ServiceType.WEB_DEVELOPMENT.value == "web_development"
        assert ServiceType.AI_SOLUTIONS.value == "ai_solutions"
        assert ServiceType.SEO.value == "seo"
        assert ServiceType.CONTENT_MARKETING.value == "content_marketing"
        assert ServiceType.ECOMMERCE.value == "ecommerce"
        assert ServiceType.LEAD_GENERATION.value == "lead_generation"
        assert ServiceType.OTHER.value == "other"
    
    def test_project_status_enum(self):
        """Test ProjectStatus enum values"""
        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.IN_PROGRESS.value == "in_progress"
        assert ProjectStatus.REVIEW.value == "review"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.CANCELLED.value == "cancelled"
    
    def test_booking_status_enum(self):
        """Test BookingStatus enum values"""
        assert BookingStatus.PENDING.value == "pending"
        assert BookingStatus.CONFIRMED.value == "confirmed"
        assert BookingStatus.COMPLETED.value == "completed"
        assert BookingStatus.CANCELLED.value == "cancelled"
        assert BookingStatus.NO_SHOW.value == "no_show"
    
    def test_user_role_enum(self):
        """Test UserRole enum values"""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.CLIENT.value == "client"
        assert UserRole.STAFF.value == "staff"


class TestBaseDocument:
    """Test BaseDocument base model"""
    
    def test_base_document_auto_generates_id(self):
        """Test that BaseDocument generates UUID automatically"""
        doc = BaseDocument()
        assert doc.id is not None
        assert isinstance(doc.id, str)
        assert len(doc.id) > 0
    
    def test_base_document_auto_generates_timestamps(self):
        """Test that BaseDocument generates timestamps automatically"""
        doc = BaseDocument()
        assert doc.created_at is not None
        assert doc.updated_at is not None
        assert isinstance(doc.created_at, datetime)
        assert isinstance(doc.updated_at, datetime)
    
    def test_base_document_with_custom_id(self):
        """Test BaseDocument with custom ID"""
        custom_id = "custom-123"
        doc = BaseDocument(id=custom_id)
        assert doc.id == custom_id


class TestContactFormModels:
    """Test contact form models"""
    
    def test_contact_form_creation(self):
        """Test ContactForm model creation"""
        form = ContactForm(
            name="John Doe",
            email="john@example.com",
            phone="+971501234567",
            service=ServiceType.WEB_DEVELOPMENT,
            message="Need a website"
        )
        
        assert form.name == "John Doe"
        assert form.email == "john@example.com"
        assert form.status == ContactStatus.NEW
        assert form.assigned_to is None
        assert form.notes == []
    
    def test_contact_form_create_validation(self):
        """Test ContactFormCreate validation"""
        form_data = ContactFormCreate(
            name="Jane Doe",
            email="jane@example.com",
            phone="+971509876543",
            service=ServiceType.SOCIAL_MEDIA,
            message="Social media management needed"
        )
        
        assert form_data.name == "Jane Doe"
        assert form_data.service == ServiceType.SOCIAL_MEDIA
    
    def test_contact_form_update(self):
        """Test ContactFormUpdate model"""
        update = ContactFormUpdate(
            status=ContactStatus.CONTACTED,
            notes=["Called customer", "Scheduled meeting"]
        )
        
        assert update.status == ContactStatus.CONTACTED
        assert len(update.notes) == 2


class TestUserModels:
    """Test user models"""
    
    def test_user_creation(self):
        """Test User model creation"""
        user = User(
            email="user@example.com",
            password_hash="hashed_password",  # noqa: S106
            full_name="Test User",
            role=UserRole.CLIENT
        )
        
        assert user.email == "user@example.com"
        assert user.role == UserRole.CLIENT
        assert user.is_active is True
    
    def test_user_create_validation(self):
        """Test UserCreate validation"""
        user_create = UserCreate(
            email="newuser@example.com",
            password="secure_password123",  # noqa: S106
            full_name="New User",
            company="Test Corp"
        )
        
        assert user_create.email == "newuser@example.com"
        assert user_create.role == UserRole.CLIENT
        assert user_create.company == "Test Corp"
    
    def test_user_login_model(self):
        """Test UserLogin model"""
        login = UserLogin(
            email="user@example.com",
            password="password123"  # noqa: S106
        )
        
        assert login.email == "user@example.com"
        assert login.password == "password123"  # noqa: S106
    
    def test_user_response_model(self):
        """Test UserResponse model"""
        response = UserResponse(
            id="user-123",
            email="user@example.com",
            full_name="Test User",
            role=UserRole.ADMIN,
            is_active=True,
            company="Test Corp",
            phone="+971501234567",
            created_at=datetime.utcnow()
        )
        
        assert response.id == "user-123"
        assert response.role == UserRole.ADMIN


class TestPortfolioModels:
    """Test portfolio models"""
    
    def test_portfolio_creation(self):
        """Test Portfolio model creation"""
        portfolio = Portfolio(
            title="E-commerce Platform",
            description="Modern e-commerce solution",
            client_name="ABC Company",
            service_type=ServiceType.WEB_DEVELOPMENT,
            project_duration="3 months",
            results=["50% increase in sales", "Better UX"],
            images=["image1.jpg", "image2.jpg"],
            technologies=["React", "Node.js", "MongoDB"],
            testimonial="Great work!",
            is_featured=True
        )
        
        assert portfolio.title == "E-commerce Platform"
        assert portfolio.is_featured is True
        assert len(portfolio.technologies) == 3
    
    def test_portfolio_create_model(self):
        """Test PortfolioCreate validation"""
        portfolio_create = PortfolioCreate(
            title="Social Media Campaign",
            description="Viral campaign",
            client_name="XYZ Corp",
            service_type=ServiceType.SOCIAL_MEDIA,
            project_duration="2 months",
            results=["1M+ reach"],
            images=[],
            technologies=["Instagram", "Facebook"]
        )
        
        assert portfolio_create.service_type == ServiceType.SOCIAL_MEDIA
        assert portfolio_create.is_featured is False
    
    def test_portfolio_update_partial(self):
        """Test PortfolioUpdate with partial data"""
        update = PortfolioUpdate(
            is_featured=True,
            testimonial="Updated testimonial"
        )
        
        assert update.is_featured is True
        assert update.title is None


class TestBookingModels:
    """Test booking models"""
    
    def test_booking_creation(self):
        """Test Booking model creation"""
        booking = Booking(
            user_id="user-123",
            service_type=ServiceType.AI_SOLUTIONS,
            preferred_date=date(2024, 3, 15),
            preferred_time="14:00",
            duration=60,
            description="Consultation for AI implementation"
        )
        
        assert booking.user_id == "user-123"
        assert booking.status == BookingStatus.PENDING
        assert booking.duration == 60
    
    def test_booking_create_model(self):
        """Test BookingCreate validation"""
        booking_create = BookingCreate(
            service_type=ServiceType.SEO,
            preferred_date=date(2024, 3, 20),
            preferred_time="10:00",
            description="SEO consultation"
        )
        
        assert booking_create.duration == 60  # Default
        assert booking_create.service_type == ServiceType.SEO
    
    def test_booking_update_model(self):
        """Test BookingUpdate model"""
        update = BookingUpdate(
            status=BookingStatus.CONFIRMED,
            meeting_link="https://zoom.us/meeting123"
        )
        
        assert update.status == BookingStatus.CONFIRMED
        assert update.meeting_link is not None


class TestChatModels:
    """Test chat models"""
    
    def test_chat_message_creation(self):
        """Test ChatMessage model creation"""
        message = ChatMessage(
            session_id="session-123",
            user_id="user-456",
            message="Hello, I need help",
            response="How can I assist you?",
            is_from_user=True
        )
        
        assert message.session_id == "session-123"
        assert message.is_from_user is True
        assert message.metadata == {}
    
    def test_chat_message_create_model(self):
        """Test ChatMessageCreate validation"""
        message_create = ChatMessageCreate(
            session_id="session-789",
            message="What services do you offer?",
            user_id="user-123"
        )
        
        assert message_create.session_id == "session-789"
        assert message_create.user_id == "user-123"
    
    def test_chat_session_creation(self):
        """Test ChatSession model creation"""
        session = ChatSession(
            session_id="session-abc",
            user_id="user-xyz",
            title="Support Chat",
            is_active=True
        )
        
        assert session.session_id == "session-abc"
        assert session.total_messages == 0
        assert session.is_active is True


class TestContentGenerationModels:
    """Test content generation models"""
    
    def test_content_generation_creation(self):
        """Test ContentGeneration model creation"""
        content = ContentGeneration(
            user_id="user-123",
            content_type="blog",
            prompt="Write about digital marketing trends",
            generated_content="AI-generated blog post content..."
        )
        
        assert content.content_type == "blog"
        assert content.is_approved is False
    
    def test_content_generation_create_model(self):
        """Test ContentGenerationCreate validation"""
        create = ContentGenerationCreate(
            content_type="social_media",
            prompt="Create Instagram post about SEO",
            user_id="user-456"
        )
        
        assert create.content_type == "social_media"
        assert create.user_id == "user-456"


class TestServiceModels:
    """Test service models"""
    
    def test_service_creation(self):
        """Test Service model creation"""
        service = Service(
            title="Social Media Management",
            description="Full-service social media management",
            icon="📱",
            features=["Content creation", "Scheduling", "Analytics"],
            price_range="AED 2000-5000/month",
            category=ServiceType.SOCIAL_MEDIA
        )
        
        assert service.title == "Social Media Management"
        assert service.is_active is True
        assert len(service.features) == 3
    
    def test_service_create_model(self):
        """Test ServiceCreate validation"""
        service_create = ServiceCreate(
            title="SEO Optimization",
            description="Complete SEO package",
            icon="🔍",
            features=["Keyword research", "On-page SEO"],
            category=ServiceType.SEO
        )
        
        assert service_create.category == ServiceType.SEO
    
    def test_service_update_model(self):
        """Test ServiceUpdate model"""
        update = ServiceUpdate(
            is_active=False,
            price_range="AED 3000-6000/month"
        )
        
        assert update.is_active is False
        assert update.title is None


class TestTestimonialModels:
    """Test testimonial models"""
    
    def test_testimonial_creation(self):
        """Test Testimonial model creation"""
        testimonial = Testimonial(
            name="Ahmed Al-Mansoori",
            company="Dubai Enterprises",
            position="CEO",
            text="Excellent service!",
            rating=5,
            is_featured=True
        )
        
        assert testimonial.name == "Ahmed Al-Mansoori"
        assert testimonial.rating == 5
        assert testimonial.is_featured is True
    
    def test_testimonial_rating_validation(self):
        """Test testimonial rating must be 1-5"""
        testimonial = Testimonial(
            name="Test User",
            company="Test Co",
            text="Good work",
            rating=3
        )
        
        assert 1 <= testimonial.rating <= 5
    
    def test_testimonial_create_model(self):
        """Test TestimonialCreate validation"""
        create = TestimonialCreate(
            name="Sara Mohammed",
            company="Tech Startup",
            text="Outstanding results!",
            rating=5
        )
        
        assert create.rating == 5
        assert create.is_featured is False
    
    def test_testimonial_update_model(self):
        """Test TestimonialUpdate model"""
        update = TestimonialUpdate(
            is_featured=True,
            rating=4
        )
        
        assert update.is_featured is True
        assert update.rating == 4


class TestAnalyticsModel:
    """Test analytics model"""
    
    def test_analytics_creation(self):
        """Test Analytics model creation"""
        analytics = Analytics(
            page_views=1000,
            unique_visitors=500,
            contact_forms=25,
            bookings=10,
            chat_sessions=50
        )
        
        assert analytics.page_views == 1000
        assert analytics.unique_visitors == 500
        assert analytics.analytics_date is not None
    
    def test_analytics_defaults(self):
        """Test Analytics default values"""
        analytics = Analytics()
        
        assert analytics.page_views == 0
        assert analytics.unique_visitors == 0
        assert analytics.contact_forms == 0
        assert analytics.bookings == 0
        assert analytics.chat_sessions == 0


class TestEmailTemplateModel:
    """Test email template model"""
    
    def test_email_template_creation(self):
        """Test EmailTemplate model creation"""
        template = EmailTemplate(
            name="Welcome Email",
            subject="Welcome to NOWHERE Digital",
            body="<html>Welcome {{name}}!</html>",
            template_type="welcome",
            variables=["name", "email"]
        )
        
        assert template.name == "Welcome Email"
        assert template.template_type == "welcome"
        assert len(template.variables) == 2


class TestResponseModels:
    """Test response models"""
    
    def test_standard_response_success(self):
        """Test StandardResponse for success"""
        response = StandardResponse(
            success=True,
            message="Operation completed",
            data={"id": "123"}
        )
        
        assert response.success is True
        assert response.message == "Operation completed"
        assert response.data["id"] == "123"
    
    def test_standard_response_error(self):
        """Test StandardResponse for error"""
        response = StandardResponse(
            success=False,
            message="Operation failed"
        )
        
        assert response.success is False
        assert response.data is None
    
    def test_paginated_response(self):
        """Test PaginatedResponse model"""
        items = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        response = PaginatedResponse(
            items=items,
            total=100,
            page=1,
            per_page=10,
            has_next=True,
            has_prev=False
        )
        
        assert len(response.items) == 3
        assert response.total == 100
        assert response.has_next is True
        assert response.has_prev is False


class TestModelValidation:
    """Test model validation and edge cases"""
    
    def test_email_validation(self):
        """Test email validation in models"""
        # Valid email should work
        form = ContactFormCreate(
            name="Test",
            email="valid@example.com",
            phone="+971501234567",
            service=ServiceType.WEB_DEVELOPMENT,
            message="Test message"
        )
        assert form.email == "valid@example.com"
    
    def test_enum_string_conversion(self):
        """Test enum conversion from strings"""
        status = ContactStatus("new")
        assert status == ContactStatus.NEW
        
        service = ServiceType("web_development")
        assert service == ServiceType.WEB_DEVELOPMENT
    
    def test_optional_fields(self):
        """Test models with optional fields"""
        user = User(
            email="test@example.com",
            password_hash="hash",  # noqa: S106
            full_name="Test User"
        )
        
        assert user.company is None
        assert user.phone is None
    
    def test_default_values(self):
        """Test default values in models"""
        contact = ContactForm(
            name="Test",
            email="test@example.com",
            phone="+971501234567",
            service=ServiceType.OTHER,
            message="Test"
        )
        
        assert contact.status == ContactStatus.NEW
        assert contact.notes == []
        assert contact.assigned_to is None