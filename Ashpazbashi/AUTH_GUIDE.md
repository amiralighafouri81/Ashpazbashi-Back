# Authentication Guide

## Quick Reference

### Endpoints
- **Sign Up**: `POST /api/auth/users/`
- **Login**: `POST /api/auth/jwt/create/`
- **Refresh Token**: `POST /api/auth/jwt/refresh/`
- **Get Profile**: `GET /api/auth/users/me/` (requires authentication)

---

## 1. Sign Up

**Endpoint**: `POST http://127.0.0.1:8000/api/auth/users/`

**Required Fields**:
- `username` (string)
- `email` (string)
- `password` (string)
- `password_confirmation` (string, must match password)

**Optional Fields**:
- `first_name` (string)
- `last_name` (string)
- `student_number` (string, must be unique)

**Example Request**:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirmation": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Example Response**:
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 2. Login

**Endpoint**: `POST http://127.0.0.1:8000/api/auth/jwt/create/`

**Required Fields**:
- `username` (string) - can also use `email`
- `password` (string)

**Example Request**:
```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Example Response**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 3. Using Access Token

After login or signup, you'll receive an `access` token. Use it in the `Authorization` header for protected endpoints:

```
Authorization: Bearer <your_access_token>
```

**Example** (Get user profile):
```http
GET /api/auth/users/me/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 4. Refresh Token

Access tokens expire after 5 minutes (default). Use the refresh token to get a new access token:

**Endpoint**: `POST http://127.0.0.1:8000/api/auth/jwt/refresh/`

**Request**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Testing with cURL

### Sign Up
```bash
curl -X POST http://127.0.0.1:8000/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirmation": "testpass123"
  }'
```

### Login
```bash
curl -X POST http://127.0.0.1:8000/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### Get Profile (with token)
```bash
curl -X GET http://127.0.0.1:8000/api/auth/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Testing with Python

See `test_auth.py` for a complete example.

```python
import requests

# Sign up
response = requests.post('http://127.0.0.1:8000/api/auth/users/', json={
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'testpass123',
    'password_confirmation': 'testpass123'
})
tokens = response.json()

# Login
response = requests.post('http://127.0.0.1:8000/api/auth/jwt/create/', json={
    'username': 'testuser',
    'password': 'testpass123'
})
tokens = response.json()
access_token = tokens['access']

# Get profile
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://127.0.0.1:8000/api/auth/users/me/', headers=headers)
profile = response.json()
```

---

## Testing with JavaScript/Fetch

See `auth_example.js` for complete examples.

```javascript
// Login
const response = await fetch('http://127.0.0.1:8000/api/auth/jwt/create/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'testuser',
    password: 'testpass123'
  })
});

const { access, refresh } = await response.json();
localStorage.setItem('access_token', access);

// Use token for authenticated requests
const token = localStorage.getItem('access_token');
const recipesResponse = await fetch('http://127.0.0.1:8000/api/recipes/', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## Common Errors

### 400 Bad Request
- Password fields don't match
- Missing required fields
- Invalid email format
- Username/email already exists

### 401 Unauthorized
- Invalid username/password
- Token expired (use refresh token)
- Missing Authorization header

### 403 Forbidden
- Invalid or expired token
- Token not provided

---

## Notes

- Access tokens expire after **5 minutes** (configurable in settings)
- Refresh tokens expire after **1 day** (configurable in settings)
- Always store tokens securely (localStorage, sessionStorage, or httpOnly cookies)
- Never expose tokens in client-side code that's publicly accessible

