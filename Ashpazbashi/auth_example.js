/**
 * JavaScript/React Example for Signup and Login
 * Use this in your frontend application
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

// ============================================
// 1. SIGN UP
// ============================================
async function signUp(username, email, password, firstName, lastName) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        email: email,
        password: password,
        password_confirmation: password,
        first_name: firstName,
        last_name: lastName,
      }),
    });

    const data = await response.json();
    
    if (response.ok) {
      // Save tokens to localStorage
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      console.log('Signup successful!', data);
      return data;
    } else {
      console.error('Signup failed:', data);
      throw new Error(data.detail || 'Signup failed');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// ============================================
// 2. LOGIN
// ============================================
async function login(username, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/jwt/create/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        password: password,
      }),
    });

    const data = await response.json();
    
    if (response.ok) {
      // Save tokens to localStorage
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      console.log('Login successful!', data);
      return data;
    } else {
      console.error('Login failed:', data);
      throw new Error(data.detail || 'Login failed');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// ============================================
// 3. GET USER PROFILE (requires token)
// ============================================
async function getUserProfile() {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    throw new Error('No access token found. Please login first.');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/users/me/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    
    if (response.ok) {
      console.log('User profile:', data);
      return data;
    } else {
      console.error('Failed to get profile:', data);
      throw new Error(data.detail || 'Failed to get profile');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// ============================================
// 4. REFRESH TOKEN
// ============================================
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token found.');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/jwt/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh: refreshToken,
      }),
    });

    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('access_token', data.access);
      console.log('Token refreshed!');
      return data;
    } else {
      console.error('Token refresh failed:', data);
      throw new Error('Token refresh failed');
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// ============================================
// USAGE EXAMPLES
// ============================================

// Example: Sign up
// signUp('john_doe', 'john@example.com', 'SecurePass123!', 'John', 'Doe')
//   .then(() => console.log('User signed up successfully'))
//   .catch(error => console.error('Signup error:', error));

// Example: Login
// login('john_doe', 'SecurePass123!')
//   .then(() => getUserProfile())
//   .then(profile => console.log('Logged in as:', profile))
//   .catch(error => console.error('Login error:', error));

// Example: Make authenticated request
// const token = localStorage.getItem('access_token');
// fetch(`${API_BASE_URL}/api/recipes/`, {
//   headers: {
//     'Authorization': `Bearer ${token}`,
//   },
// })
//   .then(response => response.json())
//   .then(data => console.log('Recipes:', data));

