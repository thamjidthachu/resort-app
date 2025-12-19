# Google OAuth2 Integration Guide

This guide explains how to set up and use Google OAuth2 for signup and signin in the Azure Horizon Backend.

## Prerequisites

1. **Google Cloud Project**: Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. **OAuth2 Credentials**: Set up OAuth2 credentials (Web application type)
3. **Python Packages**: Already installed via `requirements.txt`

## Setup Instructions

### 1. Create Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Select **Web application**
6. Add authorized JavaScript origins:
   - `http://localhost:3000` (development)
   - `https://yourdomain.com` (production)
7. Add authorized redirect URIs:
   - `http://localhost:3000/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
8. Copy the **Client ID** and **Client Secret**

### 2. Set Environment Variables

Add these to your `.env` file:

```env
GOOGLE_OAUTH2_CLIENT_ID=your_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret_here
```

### 3. Install Dependencies

The required packages are already in `requirements.txt`:
- `google-auth==2.25.2`
- `google-auth-oauthlib==1.2.0`
- `PyJWT==2.8.1`

Install them:
```bash
pip install -r requirements.txt
```

## API Endpoints

### 1. Google Signup

**Endpoint:** `POST /api/auth/google/signup/`

**Request Body:**
```json
{
  "token": "google_id_token_from_frontend",
  "username": "desired_username",  // Optional
  "phone": "user_phone_number"     // Optional
}
```

**Response (Success - 201):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "phone": "1234567890",
    "avatar": null,
    "is_active": true
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Google signup successful."
}
```

**Response (Error - 400):**
```json
{
  "detail": "User with this email already exists. Please use login."
}
```

### 2. Google Signin

**Endpoint:** `POST /api/auth/google/signin/`

**Request Body:**
```json
{
  "token": "google_id_token_from_frontend"
}
```

**Response (Success - 200):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "phone": "1234567890",
    "avatar": null,
    "is_active": true
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Google signin successful."
}
```

**Response (Error - 404):**
```json
{
  "detail": "User with this email does not exist. Please sign up first."
}
```

## Frontend Integration Example

### Using React with `@react-oauth/google`

```jsx
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';

function LoginComponent() {
  const handleGoogleSignup = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: credentialResponse.credential,
          username: 'optional_username',
          phone: 'optional_phone'
        })
      });
      
      const data = await response.json();
      if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        console.error('Signup failed:', data.detail);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleGoogleSignin = async (credentialResponse) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/signin/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: credentialResponse.credential
        })
      });
      
      const data = await response.json();
      if (response.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        console.error('Signin failed:', data.detail);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <GoogleOAuthProvider clientId="your_google_client_id">
      <div>
        <h2>Sign Up with Google</h2>
        <GoogleLogin
          onSuccess={handleGoogleSignup}
          onError={() => console.log('Signup failed')}
        />
        
        <h2>Sign In with Google</h2>
        <GoogleLogin
          onSuccess={handleGoogleSignin}
          onError={() => console.log('Signin failed')}
        />
      </div>
    </GoogleOAuthProvider>
  );
}

export default LoginComponent;
```

## How It Works

### Token Verification Flow

1. **Frontend**: User clicks "Sign in with Google"
2. **Google**: User authenticates with Google and gets an ID token
3. **Frontend**: Sends ID token to your backend
4. **Backend**: Verifies the token using `GoogleAuthService.verify_google_token()`
5. **Backend**: Extracts user info from token (email, name, etc.)
6. **Backend**: Checks if user exists
   - **Signup**: Creates new user if doesn't exist
   - **Signin**: Logs in existing user
7. **Backend**: Generates JWT tokens and returns them
8. **Frontend**: Stores tokens and redirects to dashboard

### Security Considerations

1. **Token Validation**: Tokens are verified using Google's official library
2. **Audience Check**: Ensures token is meant for your application
3. **Email Verification**: Google provides verified email status
4. **HTTPS Only**: Always use HTTPS in production
5. **CORS Configuration**: Ensure CORS is properly configured for your frontend

## Troubleshooting

### Invalid Token Error
- Ensure `GOOGLE_OAUTH2_CLIENT_ID` in settings matches the Google Cloud credentials
- Verify the token is freshly generated (tokens expire)
- Check that the token wasn't tampered with

### User Not Found Error (Signin)
- User must sign up first
- Ensure signup was successful
- Check database for the user record

### CORS Errors
- Update `CORS_ALLOWED_ORIGINS` in settings
- Configure in Google Cloud Console authorized origins

### Token Verification Fails
- Verify internet connection (connects to Google servers)
- Check `requirements.txt` has all Google packages installed
- Ensure Python version is 3.7+

## File Structure

```
apps/authentication/
├── google_auth.py          # Google OAuth2 utility service
├── serializers.py          # Includes Google serializers
├── views.py                # Includes Google views
├── urls.py                 # Includes Google URL routes
└── models.py               # User model (unchanged)
```

## Additional Features

You can extend this implementation with:
- Linking Google account to existing user
- Logout functionality
- Token refresh
- User info updates from Google
- Linking multiple social accounts

## Production Checklist

- [ ] Set up Google Cloud OAuth2 credentials for production domain
- [ ] Configure HTTPS/SSL certificates
- [ ] Update `ALLOWED_HOSTS` in Django settings
- [ ] Update CORS settings for production domain
- [ ] Test email verification
- [ ] Set up error logging and monitoring
- [ ] Configure rate limiting on auth endpoints
- [ ] Set strong `SECRET_KEY` in production
- [ ] Use environment variables for sensitive data
- [ ] Test user creation and token generation
