"""
Google OAuth2 Authentication utilities
"""
import json
import requests
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from rest_framework.exceptions import ValidationError


class GoogleAuthService:
    """Service for handling Google OAuth2 authentication"""
    
    GOOGLE_OAUTH2_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v1/certs"
    
    @staticmethod
    def verify_google_token(token):
        """
        Verify Google OAuth2 token and return user information.
        
        Args:
            token: Google OAuth2 token from frontend
            
        Returns:
            dict: User information (email, name, picture, etc.)
        """
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # Token is valid
            if idinfo.get('aud') != settings.GOOGLE_OAUTH2_CLIENT_ID:
                raise ValidationError("Token audience mismatch")
            
            return {
                'email': idinfo.get('email'),
                'full_name': idinfo.get('name'),
                'google_id': idinfo.get('sub'),
                'picture': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
        except ValueError as e:
            # Invalid token
            raise ValidationError(f"Invalid Google token: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Error verifying Google token: {str(e)}")
    
    @staticmethod
    def get_user_info_from_token(token):
        """
        Alternative method to get user info using token info endpoint.
        This is useful as a fallback or for additional verification.
        """
        try:
            response = requests.get(
                GoogleAuthService.GOOGLE_OAUTH2_URL,
                params={'id_token': token}
            )
            
            if response.status_code != 200:
                raise ValidationError("Invalid Google token")
            
            return response.json()
        except Exception as e:
            raise ValidationError(f"Error getting user info: {str(e)}")
