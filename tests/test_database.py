"""
Unit tests for backend/database.py
Tests database connection, initialization, and index creation
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.database import (
    Database,
    db,
    connect_to_db,
    close_db_connection,
    create_indexes,
    get_database
)


class TestDatabase:
    """Test Database class"""
    
    def test_database_initialization(self):
        """Test that Database class initializes with None values"""
        test_db = Database()
        assert test_db.client is None
        assert test_db.db is None
    
    def test_global_db_instance_exists(self):
        """Test that global db instance exists"""
        assert db is not None
        assert isinstance(db, Database)


class TestConnectToDb:
    """Test database connection"""
    
    @pytest.mark.asyncio
    async def test_connect_to_db_success(self):
        """Test successful database connection"""
        with patch('backend.database.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_admin = AsyncMock()
            mock_admin.command = AsyncMock(return_value={"ok": 1})
            mock_client.admin = mock_admin
            mock_client.__getitem__ = Mock(return_value=AsyncMock())
            mock_client_class.return_value = mock_client
            
            with patch('backend.database.create_indexes', new_callable=AsyncMock) as mock_indexes:
                await connect_to_db()
                
                assert db.client is not None
                assert db.db is not None
                mock_admin.command.assert_called_once_with('ping')
                mock_indexes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_to_db_failure(self):
        """Test database connection failure"""
        with patch('backend.database.AsyncIOMotorClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await connect_to_db()
            
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connect_to_db_ping_failure(self):
        """Test database connection with ping failure"""
        with patch('backend.database.AsyncIOMotorClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_admin = AsyncMock()
            mock_admin.command = AsyncMock(side_effect=Exception("Ping failed"))
            mock_client.admin = mock_admin
            mock_client_class.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                await connect_to_db()
            
            assert "Ping failed" in str(exc_info.value)


class TestCloseDbConnection:
    """Test database connection closing"""
    
    @pytest.mark.asyncio
    async def test_close_db_connection_with_client(self):
        """Test closing database connection when client exists"""
        mock_client = Mock()
        mock_client.close = Mock()
        db.client = mock_client
        
        await close_db_connection()
        
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_db_connection_without_client(self):
        """Test closing database connection when no client exists"""
        db.client = None
        
        # Should not raise any exception
        await close_db_connection()
        
        assert db.client is None


class TestCreateIndexes:
    """Test index creation"""
    
    @pytest.mark.asyncio
    async def test_create_indexes_success(self):
        """Test successful index creation on all collections"""
        mock_db = AsyncMock()
        
        # Mock collections
        collections = [
            'contact_forms', 'users', 'portfolio', 'bookings',
            'chat_messages', 'chat_sessions', 'services',
            'testimonials', 'analytics'
        ]
        
        for collection_name in collections:
            mock_collection = AsyncMock()
            mock_collection.create_index = AsyncMock(return_value=f"{collection_name}_idx")
            setattr(mock_db, collection_name, mock_collection)
        
        db.db = mock_db
        
        await create_indexes()
        
        # Verify indexes were created
        mock_db.contact_forms.create_index.assert_called()
        mock_db.users.create_index.assert_called()
        mock_db.portfolio.create_index.assert_called()
        mock_db.bookings.create_index.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_indexes_failure(self):
        """Test index creation failure handling"""
        mock_db = AsyncMock()
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock(side_effect=Exception("Index creation failed"))
        mock_db.contact_forms = mock_collection
        mock_db.users = mock_collection
        mock_db.portfolio = mock_collection
        mock_db.bookings = mock_collection
        mock_db.chat_messages = mock_collection
        mock_db.chat_sessions = mock_collection
        mock_db.services = mock_collection
        mock_db.testimonials = mock_collection
        mock_db.analytics = mock_collection
        
        db.db = mock_db
        
        # Should not raise exception, just log error
        await create_indexes()
    
    @pytest.mark.asyncio
    async def test_create_unique_indexes(self):
        """Test creation of unique indexes"""
        mock_db = AsyncMock()
        
        mock_users = AsyncMock()
        mock_users.create_index = AsyncMock()
        mock_db.users = mock_users
        
        mock_sessions = AsyncMock()
        mock_sessions.create_index = AsyncMock()
        mock_db.chat_sessions = mock_sessions
        
        mock_analytics = AsyncMock()
        mock_analytics.create_index = AsyncMock()
        mock_db.analytics = mock_analytics
        
        # Mock other collections
        for collection in ['contact_forms', 'portfolio', 'bookings', 
                          'chat_messages', 'services', 'testimonials']:
            mock_collection = AsyncMock()
            mock_collection.create_index = AsyncMock()
            setattr(mock_db, collection, mock_collection)
        
        db.db = mock_db
        
        await create_indexes()
        
        # Verify unique indexes were requested
        # Users email should be unique
        calls = mock_users.create_index.call_args_list
        assert any('email' in str(call) and 'unique' in str(call) for call in calls)


class TestGetDatabase:
    """Test get_database function"""
    
    def test_get_database_returns_db(self):
        """Test that get_database returns the database instance"""
        mock_db_instance = Mock()
        db.db = mock_db_instance
        
        result = get_database()
        
        assert result is mock_db_instance
    
    def test_get_database_returns_none_when_not_connected(self):
        """Test get_database when database is not connected"""
        db.db = None
        
        result = get_database()
        
        assert result is None


class TestDatabaseIndexConfiguration:
    """Test specific index configurations"""
    
    @pytest.mark.asyncio
    async def test_contact_forms_indexes(self):
        """Test contact forms collection indexes"""
        mock_db = AsyncMock()
        mock_contact_forms = AsyncMock()
        mock_contact_forms.create_index = AsyncMock()
        mock_db.contact_forms = mock_contact_forms
        
        # Mock other collections
        for collection in ['users', 'portfolio', 'bookings', 'chat_messages',
                          'chat_sessions', 'services', 'testimonials', 'analytics']:
            mock_collection = AsyncMock()
            mock_collection.create_index = AsyncMock()
            setattr(mock_db, collection, mock_collection)
        
        db.db = mock_db
        
        await create_indexes()
        
        # Verify contact_forms indexes
        assert mock_contact_forms.create_index.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_bookings_indexes(self):
        """Test bookings collection indexes"""
        mock_db = AsyncMock()
        mock_bookings = AsyncMock()
        mock_bookings.create_index = AsyncMock()
        mock_db.bookings = mock_bookings
        
        # Mock other collections
        for collection in ['users', 'portfolio', 'contact_forms', 'chat_messages',
                          'chat_sessions', 'services', 'testimonials', 'analytics']:
            mock_collection = AsyncMock()
            mock_collection.create_index = AsyncMock()
            setattr(mock_db, collection, mock_collection)
        
        db.db = mock_db
        
        await create_indexes()
        
        # Verify bookings indexes (user_id, status, preferred_date)
        assert mock_bookings.create_index.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_chat_messages_indexes(self):
        """Test chat messages collection indexes"""
        mock_db = AsyncMock()
        mock_chat_messages = AsyncMock()
        mock_chat_messages.create_index = AsyncMock()
        mock_db.chat_messages = mock_chat_messages
        
        # Mock other collections
        for collection in ['users', 'portfolio', 'contact_forms', 'bookings',
                          'chat_sessions', 'services', 'testimonials', 'analytics']:
            mock_collection = AsyncMock()
            mock_collection.create_index = AsyncMock()
            setattr(mock_db, collection, mock_collection)
        
        db.db = mock_db
        
        await create_indexes()
        
        # Verify chat_messages indexes (session_id, user_id, created_at)
        assert mock_chat_messages.create_index.call_count >= 3


class TestDatabaseConnectionConfiguration:
    """Test database connection configuration"""
    
    @pytest.mark.asyncio
    async def test_connect_uses_settings_mongo_url(self):
        """Test that connect_to_db uses mongo_url from settings"""
        with patch('backend.database.AsyncIOMotorClient') as mock_client_class:
            with patch('backend.database.settings') as mock_settings:
                mock_settings.mongo_url = "mongodb://custom:27017"
                mock_settings.db_name = "custom_db"
                
                mock_client = AsyncMock()
                mock_admin = AsyncMock()
                mock_admin.command = AsyncMock(return_value={"ok": 1})
                mock_client.admin = mock_admin
                mock_client.__getitem__ = Mock(return_value=AsyncMock())
                mock_client_class.return_value = mock_client
                
                with patch('backend.database.create_indexes', new_callable=AsyncMock):
                    await connect_to_db()
                
                mock_client_class.assert_called_once_with("mongodb://custom:27017")
    
    @pytest.mark.asyncio
    async def test_connect_uses_settings_db_name(self):
        """Test that connect_to_db uses db_name from settings"""
        with patch('backend.database.AsyncIOMotorClient') as mock_client_class:
            with patch('backend.database.settings') as mock_settings:
                mock_settings.mongo_url = "mongodb://localhost:27017"
                mock_settings.db_name = "custom_database"
                
                mock_client = AsyncMock()
                mock_admin = AsyncMock()
                mock_admin.command = AsyncMock(return_value={"ok": 1})
                mock_client.admin = mock_admin
                
                mock_db = AsyncMock()
                mock_client.__getitem__ = Mock(return_value=mock_db)
                mock_client_class.return_value = mock_client
                
                with patch('backend.database.create_indexes', new_callable=AsyncMock):
                    await connect_to_db()
                
                mock_client.__getitem__.assert_called_once_with("custom_database")