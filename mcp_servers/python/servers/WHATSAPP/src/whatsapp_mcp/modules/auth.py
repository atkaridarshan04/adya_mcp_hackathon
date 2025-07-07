"""Authentication module for WhatsApp MCP Server."""

import logging
import os
from typing import Dict, Tuple, Any, Optional

from dotenv import load_dotenv


# Import the WhatsApp API client
from whatsapp_api_client_python.API import GreenApi

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp client implementation using whatsapp-api-client-python."""

    def __init__(self, id_instance: Optional[str] = None, api_token: Optional[str] = None) -> None:
        self.is_authenticated = False
        self.session_data: Dict[str, Any] = {}
        self.client = None
        self.qr_code = None
        self.state = "DISCONNECTED"
        self.id_instance = id_instance
        self.api_token = api_token

    async def initialize(self) -> bool:
        """Initialize the client."""
        logger.info("Initializing WhatsApp client")
        try:
            # Use provided credentials first, then fall back to environment variables
            id_instance = self.id_instance or os.getenv("GREENAPI_ID_INSTANCE")
            api_token_instance = self.api_token or os.getenv("GREENAPI_API_TOKEN")

            if not id_instance or not api_token_instance:
                logger.error(
                    "Missing required credentials: GREENAPI_ID_INSTANCE or GREENAPI_API_TOKEN. "
                    "Please provide them either as environment variables or through the __credentials__ parameter."
                )
                return False

            self.client = GreenApi(
                idInstance=id_instance, apiTokenInstance=api_token_instance
            )
            
            # Test the connection by getting account settings
            try:
                settings = self.client.account.getSettings()
                if settings:
                    logger.info("WhatsApp client initialized successfully")
                    self.is_authenticated = True
                    return True
                else:
                    logger.error("Failed to get account settings - invalid credentials")
                    return False
            except Exception as e:
                logger.error(f"Failed to validate credentials: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp client: {e}")
            return False


class AuthManager:
    """Manager for authentication-related operations."""

    def __init__(self) -> None:
        self.session: WhatsAppClient | None = None

    async def open_session(self, credentials: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """
        Open a new session.
        
        Args:
            credentials: Optional dictionary containing GREENAPI_ID_INSTANCE and GREENAPI_API_TOKEN
        """
        if self.session:
            return False, "Session already exists"

        # Extract credentials if provided
        id_instance = None
        api_token = None
        
        if credentials:
            id_instance = credentials.get("GREENAPI_ID_INSTANCE")
            api_token = credentials.get("GREENAPI_API_TOKEN")
            
            # Filter out None values
            if not id_instance:
                id_instance = None
            if not api_token:
                api_token = None

        client = WhatsAppClient(id_instance=id_instance, api_token=api_token)
        success = await client.initialize()

        if success:
            self.session = client
            return True, "Session created successfully and authenticated with WhatsApp API"

        return False, "Failed to create session - please check your credentials"

    def is_authenticated(self) -> bool:
        """Check if a session is authenticated."""
        return self.session is not None and self.session.is_authenticated

    def get_client(self) -> WhatsAppClient | None:
        """Get the client for a session."""
        return self.session

    def close_session(self) -> Tuple[bool, str]:
        """Close the current session."""
        if not self.session:
            return False, "No active session to close"
        
        self.session = None
        return True, "Session closed successfully"

    def get_session_status(self) -> Dict[str, Any]:
        """Get the current session status."""
        if not self.session:
            return {
                "authenticated": False,
                "state": "DISCONNECTED",
                "message": "No active session"
            }
        
        return {
            "authenticated": self.session.is_authenticated,
            "state": self.session.state,
            "message": "Session active" if self.session.is_authenticated else "Session not authenticated"
        }


# Create a singleton instance
auth_manager = AuthManager()
