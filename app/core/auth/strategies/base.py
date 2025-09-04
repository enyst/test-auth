from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request
from app.models.user import User


class AuthStrategy(ABC):
    """Base authentication strategy"""
    
    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[User]:
        """
        Authenticate a request and return the user if successful.
        Returns None if authentication fails or is not required.
        """
        pass
    
    @abstractmethod
    def get_login_url(self) -> Optional[str]:
        """
        Get the login URL for this authentication strategy.
        Returns None if no login is required.
        """
        pass
    
    @abstractmethod
    def requires_auth(self) -> bool:
        """
        Check if this strategy requires authentication.
        """
        pass