"""Authenticate and handle users"""

# For now we just use a simple static token. TODO: Replace with user list
COMMON_TOKEN = "test123"

class User:
    """Class representing a user with some basic info and auth. method"""
    def __init__(self):
        self.is_authenticated = False

    def authenticate(self, client_id, token):
        """Check if user is valid"""
        if client_id is not None and token == COMMON_TOKEN:
            self.is_authenticated = True
