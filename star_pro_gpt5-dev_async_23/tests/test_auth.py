import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI Auth Backend"}


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_signup():
    """Test user signup"""
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "username": "Test User"
    }
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data


def test_login():
    """Test user login"""
    # First create a user
    user_data = {
        "email": "login@example.com",
        "password": "password123",
        "username": "Login User"
    }
    client.post("/auth/signup", json=user_data)
    
    # Then login
    login_data = {
        "email": "login@example.com",
        "password": "password123"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_signup_duplicate_email():
    """Test signup with duplicate email"""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123",
        "username": "Duplicate User"
    }
    # Create user first time
    client.post("/auth/signup", json=user_data)
    
    # Try to create user with same email
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 400
