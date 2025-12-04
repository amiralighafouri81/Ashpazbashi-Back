#!/bin/bash
# Test Signup and Login endpoints

BASE_URL="http://127.0.0.1:8000"

echo "=== 1. SIGN UP ==="
curl -X POST "$BASE_URL/api/auth/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirmation": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

echo -e "\n\n=== 2. LOGIN ==="
curl -X POST "$BASE_URL/api/auth/jwt/create/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

echo -e "\n\n=== 3. GET USER PROFILE (requires token) ==="
# Replace YOUR_ACCESS_TOKEN with the token from login response
# curl -X GET "$BASE_URL/api/auth/users/me/" \
#   -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

