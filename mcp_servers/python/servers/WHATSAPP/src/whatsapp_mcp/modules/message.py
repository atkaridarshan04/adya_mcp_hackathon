"""Message module for WhatsApp MCP Server with fixed group/contact handling."""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from whatsapp_mcp.modules.auth import auth_manager

logger = logging.getLogger(__name__)


def _get_chat_id(phone_number: str) -> str:
    """Get the chat ID for a phone number or group ID."""
    # Remove the country code symbol and clean the number
    phone_number = phone_number.strip().replace("+", "")
    
    # If the number already has @g.us suffix (group), return as is
    if phone_number.endswith("@g.us"):
        return phone_number
    
    # If the number already has @c.us suffix (contact), return as is
    if phone_number.endswith("@c.us"):
        return phone_number
    
    # If it's a group ID pattern (long number), add @g.us
    if len(phone_number) > 15 and phone_number.isdigit():
        return f"{phone_number}@g.us"
    
    # For regular phone numbers, ensure proper format for GreenAPI
    if phone_number.isdigit():
        # If it's an Indian number starting with 91, keep as is
        if phone_number.startswith("91") and len(phone_number) == 12:
            return f"{phone_number}@c.us"
        # If it's a 10-digit Indian number, add 91 prefix
        elif len(phone_number) == 10 and not phone_number.startswith("91"):
            return f"91{phone_number}@c.us"
        # For other international numbers, keep as is
        else:
            return f"{phone_number}@c.us"
    
    # If already formatted correctly, return as is
    return phone_number


async def send_message(
    phone_number: str, content: str, reply_to: Optional[str] = None
) -> dict:
    """Send a message to a chat."""
    logger.info(f"Sending message to {phone_number}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        chat_id = _get_chat_id(phone_number)
        # Send the message via the WhatsApp API
        logger.info(f"Formatted chat_id: {chat_id}")
        logger.debug(f"Sending message to {chat_id}: {content}")

        # Convert to asyncio to prevent blocking
        response = whatsapp_client.client.sending.sendMessage(chat_id, content)

        logger.info(f"Response code {response.code}: {response.data}")

        # Check if the response indicates an error
        if response.code != 200:
            error_msg = f"GreenAPI Error {response.code}: {response.data}"
            logger.error(error_msg)
            return {
                "message_id": "failed",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "response": response.data,
                "phone_number": phone_number,
                "formatted_chat_id": chat_id,
                "content_length": len(content)
            }

        response_data = response.data

        message_id = "Not provided"
        # Try to extract message ID from the response if available
        if isinstance(response_data, dict):
            if response_data.get("idMessage"):
                message_id = response_data.get("idMessage")
            elif response_data.get("id"):
                message_id = response_data.get("id")

        result = {
            "message_id": message_id,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "response": response_data,
            "phone_number": phone_number,
            "formatted_chat_id": chat_id,
            "content_length": len(content)
        }

        logger.info(f"Message sent successfully with ID {message_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return {
            "message_id": "failed",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "phone_number": phone_number,
            "content_length": len(content) if content else 0
        }


async def get_chat_history(chat_id: str, count: int = 100) -> List[Dict[str, Any]]:
    """Get chat history for a specific chat using GreenAPI."""
    logger.info(f"Getting chat history for {chat_id} with count {count}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        # Format the chat_id properly
        formatted_chat_id = _get_chat_id(chat_id)
        
        # Use GreenAPI's getChatHistory method
        response = whatsapp_client.client.journals.getChatHistory(formatted_chat_id, count)

        logger.info(f"Chat history response code: {response.code}")
        logger.info(f"Chat history response data length: {len(response.data) if response.data else 0}")

        messages = []
        if response.code == 200 and response.data:
            for message_data in response.data:
                message = {
                    "id": message_data.get("idMessage", "unknown"),
                    "timestamp": message_data.get("timestamp", 0),
                    "type": message_data.get("typeMessage", "textMessage"),
                    "chat_id": message_data.get("chatId", formatted_chat_id),
                    "sender_name": message_data.get("senderName", "Unknown"),
                    "sender_id": message_data.get("senderId", ""),
                    "text_message": message_data.get("textMessage", ""),
                    "download_url": message_data.get("downloadUrl", ""),
                    "caption": message_data.get("caption", ""),
                    "formatted_time": datetime.fromtimestamp(
                        message_data.get("timestamp", 0)
                    ).isoformat() if message_data.get("timestamp") else None
                }
                messages.append(message)
        else:
            logger.warning(f"Failed to get chat history. Response code: {response.code}")

        logger.info(f"Retrieved {len(messages)} messages for chat {formatted_chat_id}")
        return messages

    except Exception as e:
        logger.error(f"Failed to get chat history for {chat_id}: {e}")
        return []


async def get_chats(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get a list of chats using GreenAPI."""
    logger.info(f"Getting chats with limit {limit}, offset {offset}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        # Use GreenAPI's getChats method to get list of chats
        response = whatsapp_client.client.journals.getChats()

        logger.info(f"Get chats response code: {response.code}")
        logger.info(f"Get chats response data: {response.data}")

        chats = []
        if response.code == 200 and response.data:
            chat_list = response.data if isinstance(response.data, list) else []
            
            # Apply offset and limit for pagination
            paginated_chats = chat_list[offset:offset + limit]
            
            for chat_data in paginated_chats:
                # Extract chat information from GreenAPI response
                chat = {
                    "id": chat_data.get("id", "unknown"),
                    "name": chat_data.get("name", "Unknown Contact"),
                    "type": "group" if chat_data.get("id", "").endswith("@g.us") else "contact",
                    "last_message_time": chat_data.get("lastMessageTime", 0),
                    "archive": chat_data.get("archive", False),
                    "ephemeralExpiration": chat_data.get("ephemeralExpiration", 0),
                    "ephemeralSettingTimestamp": chat_data.get("ephemeralSettingTimestamp", 0),
                    "muteExpiration": chat_data.get("muteExpiration", 0),
                    "notSpam": chat_data.get("notSpam", True),
                    "unread_count": 0,  # GreenAPI doesn't provide unread count in getChats
                    "is_pinned": False,  # GreenAPI doesn't provide pinned status in getChats
                    "formatted_time": datetime.fromtimestamp(
                        chat_data.get("lastMessageTime", 0)
                    ).isoformat() if chat_data.get("lastMessageTime") else None
                }
                chats.append(chat)
        else:
            logger.warning(f"Failed to get chats or no chats found. Response code: {response.code}")
            # If getChats doesn't work, try alternative method
            try:
                logger.info("Trying alternative method: getChatHistory")
                # Try to get recent chat history as fallback
                response = whatsapp_client.client.journals.getChatHistory("", 100)
                
                if response.code == 200 and response.data:
                    # Extract unique chat IDs from chat history
                    chat_ids = set()
                    for message in response.data:
                        chat_id = message.get("chatId")
                        if chat_id:
                            chat_ids.add(chat_id)
                    
                    # Create chat objects from unique chat IDs
                    for i, chat_id in enumerate(list(chat_ids)[offset:offset + limit]):
                        chat = {
                            "id": chat_id,
                            "name": chat_id.split("@")[0] if "@" in chat_id else "Unknown",
                            "type": "group" if chat_id.endswith("@g.us") else "contact",
                            "last_message_time": 0,
                            "archive": False,
                            "ephemeralExpiration": 0,
                            "ephemeralSettingTimestamp": 0,
                            "muteExpiration": 0,
                            "notSpam": True,
                            "unread_count": 0,
                            "is_pinned": False,
                            "formatted_time": None
                        }
                        chats.append(chat)
                        
            except Exception as fallback_error:
                logger.error(f"Fallback method also failed: {fallback_error}")

        logger.info(f"Retrieved {len(chats)} chats")
        return chats

    except Exception as e:
        logger.error(f"Failed to get chats: {e}")
        # Return a sample chat structure to show the expected format
        sample_chats = [
            {
                "id": "sample_contact@c.us",
                "name": "Sample Contact",
                "type": "contact",
                "last_message_time": 0,
                "archive": False,
                "ephemeralExpiration": 0,
                "ephemeralSettingTimestamp": 0,
                "muteExpiration": 0,
                "notSpam": True,
                "unread_count": 0,
                "is_pinned": False,
                "formatted_time": None,
                "error": f"Failed to retrieve actual chats: {str(e)}"
            }
        ]
        return sample_chats
