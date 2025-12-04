"""
Test script for Signup and Login
Run: python test_auth.py
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. SIGN UP
print("=== 1. SIGN UP ===")
signup_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirmation": "testpass123",
    "first_name": "Test",
    "last_name": "User"
}

response = requests.post(f"{BASE_URL}/api/auth/users/", json=signup_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

if response.status_code == 201:
    user_data = response.json()
    access_token = user_data.get('access')
    refresh_token = user_data.get('refresh')
    
    # 2. LOGIN
    print("=== 2. LOGIN ===")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/jwt/create/", json=login_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access')
        
        # 3. GET USER PROFILE (requires authentication)
        print("=== 3. GET USER PROFILE ===")
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(f"{BASE_URL}/api/auth/users/me/", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")

