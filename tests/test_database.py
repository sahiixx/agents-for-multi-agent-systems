"""
Unit tests for backend/database.py
Tests database connection and initialization
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.database import Database, get_database, db, connect_to_db, close_db_connection


class TestDatabase:
    """Test suite for Database class"""
    
    @pytest.fixture
    def database(self):
        """Create database instance for testing"""
        return Database()
    
    def test_initialization(self, database):
        """Test database initialization"""
        assert database.client is None
        assert database.db is None
        
    @pytest.mark.asyncio
    @patch('backend.database.AsyncIOMotorClient')
    @patch('backend.database.settings')
    async def test_connect(self, mock_settings, mock_client_class):
        """Test database connection via module function"""
        mock_settings.mongo_url = "mongodb://localhost:27017"
        mock_settings.db_name = "test_db"
        mock_client = Mock()
        mock_client.admin = Mock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})
        mock_db = Mock()
        mock_client.__getitem__ = Mock(return_value=mock_db)
        mock_client_class.return_value = mock_client
        await connect_to_db()
        assert db.client is not None
        
        await db.close()
        
        db.client.close.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_close(self):
        """Test database connection closing via module function"""
        db.client = Mock()
        db.client.close = Mock()
        await close_db_connection()
        db.client.close.assert_called_once()
        """Test get_database returns database instance"""
        result = get_database()
        assert result is not None
        
    def test_db_global_instance_exists(self):
        """Test global db instance exists"""
        assert db is not None
        assert isinstance(db, Database)