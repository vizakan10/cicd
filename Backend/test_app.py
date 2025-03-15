import os
import sys
import pytest
import mongomock
from unittest.mock import patch, MagicMock
from flask import Flask

# Import the app
from app import app

@pytest.fixture
def client():
    """Create a test client for the app."""
    # Configure the app for testing
    app.config.update({
        "TESTING": True,
        "MONGO_URI": "mongodb://localhost:27017/testdb",  # Test URI
        "SECRET_KEY": "test_secret_key"
    })
    
    # Create a mock MongoDB client and collection
    mock_db = mongomock.MongoClient().db
    mock_collection = mock_db.sp1
    
    # Add a test user to the mocked collection
    test_user = {
        "email": "test@example.com",
        "password": "hashed_password",  # This would be a hashed password in reality
        "name": "Test User",
        "custom_words": [],
        "selected_sounds": ["p", "b"],
        "total_score": 0,
        "level": 1,
        "scores": []
    }
    mock_collection.insert_one(test_user)
    
    # Patch the global collection reference in the app module
    with patch('app.collection', mock_collection):
        # Create a test client
        with app.test_client() as testing_client:
            # Create app context for testing
            with app.app_context():
                yield testing_client

def test_login(client):
    # Mock check_password_hash to always return True for testing
    with patch('app.check_password_hash', return_value=True):
        response = client.post('/login', json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["message"] == "Login successful"

def test_get_target_word(client):
    # Set user_email in session
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    # Mock random.choice to return a predictable word
    with patch('random.choice', return_value='Pencil'):
        response = client.get('/get-target-word')
        assert response.status_code == 200
        data = response.get_json()
        assert 'target_word' in data
        assert data['target_word'] == 'Pencil'

def test_dashboard(client):
    # Set user_email in session
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.get('/dashboard')
    assert response.status_code == 200
    data = response.get_json()
    assert 'streak' in data
    assert 'accuracy' in data
    assert 'words_mastered' in data
    assert 'level' in data
    assert 'weekly_trend' in data

def test_update_selected_sounds(client):
    # Set user_email in session
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.post('/update_selected_sounds', json={
        "selected_sounds": ["p", "t", "k"]
    })
    assert response.status_code == 200

def test_add_custom_word(client):
    # Set user_email in session
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.post('/add-custom-word', json={
        "custom_word": "TestWord"
    })
    assert response.status_code == 200
    assert "message" in response.get_json()

# Add these test functions to your existing test_app.py file

def test_login_invalid_credentials(client):
    """Test login with invalid password"""
    # Mock check_password_hash to return False (invalid password)
    with patch('app.check_password_hash', return_value=False):
        response = client.post('/login', json={
            "email": "test@example.com",
            "password": "wrong_password"
        })
        assert response.status_code == 401
        data = response.get_json()
        assert "message" in data
        assert data["message"] == "Invalid password"

def test_login_user_not_found(client):
    """Test login with non-existent user"""
    response = client.post('/login', json={
        "email": "nonexistent@example.com",
        "password": "password123"
    })
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data
    assert data["message"] == "User not found"

def test_login_missing_fields(client):
    """Test login with missing required fields"""
    response = client.post('/login', json={
        "email": "test@example.com"
        # Missing password
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data
    assert "required" in data["message"].lower()

def test_get_target_word_not_authenticated(client):
    """Test getting target word without authentication"""
    response = client.get('/get-target-word')
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    # The actual error message is "User not logged in. Please log in first."
    assert "not logged in" in data["error"].lower()

def test_dashboard_not_authenticated(client):
    """Test accessing dashboard without authentication"""
    response = client.get('/dashboard')
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    # The actual error message is "User not logged in. Please log in first."
    assert "not logged in" in data["error"].lower()
def test_update_selected_sounds_not_authenticated(client):
    """Test updating selected sounds without authentication"""
    response = client.post('/update_selected_sounds', json={
        "selected_sounds": ["p", "t", "k"]
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_update_selected_sounds_missing_data(client):
    """Test updating selected sounds with missing data"""
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.post('/update_selected_sounds', json={
        # Missing selected_sounds field
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

def test_add_custom_word_missing_word(client):
    """Test adding a custom word with missing word data"""
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.post('/add-custom-word', json={
        # Missing custom_word field
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "required" in data["error"].lower()

def test_speech_to_text_no_audio(client):
    """Test speech-to-text endpoint with no audio file"""
    with client.session_transaction() as session:
        session['user_email'] = 'test@example.com'
    
    response = client.post('/speech-to-text')
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "no audio file" in data["error"].lower()

def test_register_user_already_exists(client):
    """Test registering a user that already exists"""
    response = client.post('/register', json={
        "name": "Test User",
        "email": "test@example.com",  # This email already exists in our mock DB
        "password": "password123"
    })
    assert response.status_code == 409
    data = response.get_json()
    assert "message" in data
    assert "already exists" in data["message"].lower()

def test_register_missing_fields(client):
    """Test registering a user with missing required fields"""
    response = client.post('/register', json={
        "name": "Test User",
        # Missing email and password
    })
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "required" in data["error"].lower()