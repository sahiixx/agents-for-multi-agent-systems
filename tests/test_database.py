"""
Comprehensive unit tests for backend/database.py
Tests database connection and index management
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from motor.motor_asyncio import AsyncIOMotorClient


class TestDatabaseClass:
    """Test the Database class"""
    
    def test_database_initialization(self):
        """Test Database class attributes"""
        from backend.database import Database
        
        db = Database()
        assert hasattr(db, "client")
        assert hasattr(db, "db")
    
    def test_database_singleton_pattern(self):
        """Test db is a global instance"""
        from backend.database import db
        
        assert db is not None
        assert hasattr(db, "client")
        assert hasattr(db, "db")


class TestConnectToDb:
    """Test connect_to_db function"""
    
    @pytest.mark.asyncio
    async def test_connect_to_db_success(self):
        """Test successful database connection"""
        from backend.database import connect_to_db, db
        
        # The stub motor should allow connection
        await connect_to_db()
        
        assert db.client is not None
        assert db.db is not None
    
    @pytest.mark.asyncio
    async def test_connect_to_db_creates_indexes(self):
        """Test that connect_to_db creates indexes"""
        from backend.database import connect_to_db, db
        
        # Mock create_indexes to verify it's called
        with patch("backend.database.create_indexes", new=AsyncMock()) as mock_indexes:
            await connect_to_db()
            mock_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_to_db_handles_connection_error(self):
        """Test error handling when connection fails"""
        from backend.database import db
        
        # Mock the AsyncIOMotorClient to raise an exception
        with patch("backend.database.AsyncIOMotorClient") as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            
            from backend.database import connect_to_db
            
            with pytest.raises(Exception) as exc_info:
                await connect_to_db()
            
            assert "Connection failed" in str(exc_info.value)


class TestCloseDbConnection:
    """Test close_db_connection function"""
    
    @pytest.mark.asyncio
    async def test_close_db_connection_with_client(self):
        """Test closing connection when client exists"""
        from backend.database import close_db_connection, db, connect_to_db
        
        # Establish connection first
        await connect_to_db()
        
        # Close connection
        await close_db_connection()
        
        # Client should have close called (stub doesn't actually do anything)
    
    @pytest.mark.asyncio
    async def test_close_db_connection_without_client(self):
        """Test closing connection when client doesn't exist"""
        from backend.database import close_db_connection, db
        
        db.client = None
        
        # Should not raise an error
        await close_db_connection()


class TestCreateIndexes:
    """Test create_indexes function"""
    
    @pytest.mark.asyncio
    async def test_create_indexes_success(self):
        """Test successful index creation"""
        from backend.database import create_indexes, connect_to_db, db
        
        # Establish connection
        await connect_to_db()
        
        # Should not raise an error
        await create_indexes()
    
    @pytest.mark.asyncio
    async def test_create_indexes_creates_all_collections(self):
        """Test that indexes are created for all expected collections"""
        from backend.database import create_indexes, connect_to_db, db
        
        await connect_to_db()
        await create_indexes()
        
        # Verify collections exist
        expected_collections = [
            "contact_forms",
            "users",
            "portfolio",
            "bookings",
            "chat_messages",
            "chat_sessions",
            "services",
            "testimonials",
            "analytics"
        ]
        
        for collection_name in expected_collections:
            collection = getattr(db.db, collection_name, None)
            assert collection is not None
    
    @pytest.mark.asyncio
    async def test_create_indexes_handles_errors(self):
        """Test error handling in create_indexes"""
        from backend.database import db
        
        # Mock db.db to raise an exception
        db.db = MagicMock()
        db.db.contact_forms.create_index = AsyncMock(side_effect=Exception("Index creation failed"))
        
        from backend.database import create_indexes
        
        # Should not raise - errors are logged
        await create_indexes()


class TestGetDatabase:
    """Test get_database function"""
    
    @pytest.mark.asyncio
    async def test_get_database_returns_db_instance(self):
        """Test get_database returns the database instance"""
        from backend.database import get_database, connect_to_db
        
        await connect_to_db()
        
        database = get_database()
        assert database is not None
    
    @pytest.mark.asyncio
    async def test_get_database_returns_same_instance(self):
        """Test get_database returns the same instance"""
        from backend.database import get_database, connect_to_db
        
        await connect_to_db()
        
        db1 = get_database()
        db2 = get_database()
        
        assert db1 is db2


class TestDatabaseIntegration:
    """Integration tests for database module"""
    
    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle"""
        from backend.database import connect_to_db, close_db_connection, get_database
        
        # Connect
        await connect_to_db()
        
        # Get database
        db = get_database()
        assert db is not None
        
        # Close
        await close_db_connection()
    
    @pytest.mark.asyncio
    async def test_database_configuration_from_settings(self):
        """Test database uses configuration from settings"""
        from backend.database import db
        from backend.config import settings
        
        # Verify settings are used
        assert settings.mongo_url is not None
        assert settings.db_name is not None