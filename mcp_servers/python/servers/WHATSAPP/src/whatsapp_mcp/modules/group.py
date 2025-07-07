"""Group module for WhatsApp MCP Server."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from whatsapp_mcp.models import Contact, Group, Participant
from whatsapp_mcp.modules.auth import auth_manager

logger = logging.getLogger(__name__)


def _format_phone_number(phone: str) -> str:
    """Format phone number for WhatsApp API."""
    phone = phone.strip().replace("+", "")
    if not phone.endswith("@c.us"):
        return f"{phone}@c.us"
    return phone


async def create_group(group_name: str, participants: List[str]) -> Group:
    """Create a new WhatsApp group using GreenAPI."""
    logger.info(f"Creating group '{group_name}' with {len(participants)} participants")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    if len(participants) < 1:
        raise ValueError("Need at least one participant to create a group")

    try:
        # Format participant phone numbers correctly
        formatted_participants = [_format_phone_number(phone) for phone in participants]
        
        logger.debug(f"Creating group with participants: {formatted_participants}")

        # Use GreenAPI's createGroup method
        response = whatsapp_client.client.groups.createGroup(
            groupName=group_name,
            chatIds=formatted_participants
        )

        logger.info(f"Group creation response code: {response.code}")
        logger.info(f"Group creation response data: {response.data}")

        if response.code == 200 and response.data:
            # Extract group information from response
            group_data = response.data
            group_id = group_data.get("chatId", f"group_{uuid.uuid4().hex[:8]}")
            
            # Create Group object
            group = Group(
                id=group_id,
                name=group_name,
                participants=[
                    Participant(
                        id=phone,
                        name=phone.split("@")[0],  # Use phone number as name
                        role="member"
                    ) for phone in formatted_participants
                ],
                created_at=datetime.now().isoformat(),
                created_by="current_user"
            )
            
            logger.info(f"Group '{group_name}' created successfully with ID: {group_id}")
            return group
        else:
            error_msg = f"Failed to create group. Response code: {response.code}, Data: {response.data}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except Exception as e:
        logger.error(f"Failed to create group '{group_name}': {e}")
        # Return a Group object with error information
        return Group(
            id="error",
            name=group_name,
            participants=[],
            created_at=datetime.now().isoformat(),
            created_by="error",
            error=str(e)
        )


async def get_group_participants(group_id: str) -> List[Participant]:
    """Get participants of a WhatsApp group using GreenAPI."""
    logger.info(f"Getting participants for group: {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        # Use GreenAPI's getGroupData method
        response = whatsapp_client.client.groups.getGroupData(group_id)

        logger.info(f"Group data response code: {response.code}")
        logger.info(f"Group data response: {response.data}")

        participants = []
        
        if response.code == 200 and response.data:
            group_data = response.data
            
            # Extract participants from group data
            if "participants" in group_data:
                for participant_data in group_data["participants"]:
                    participant = Participant(
                        id=participant_data.get("id", "unknown"),
                        name=participant_data.get("name", participant_data.get("id", "Unknown")),
                        role=participant_data.get("isAdmin", False) and "admin" or "member"
                    )
                    participants.append(participant)
            else:
                logger.warning(f"No participants found in group data for {group_id}")
        else:
            error_msg = f"Failed to get group data. Response code: {response.code}, Data: {response.data}"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(f"Retrieved {len(participants)} participants for group {group_id}")
        return participants

    except Exception as e:
        logger.error(f"Failed to get participants for group {group_id}: {e}")
        # Return empty list on error
        return []


async def add_participant_to_group(group_id: str, participant_phone: str) -> bool:
    """Add a participant to a WhatsApp group using GreenAPI."""
    logger.info(f"Adding participant {participant_phone} to group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        formatted_phone = _format_phone_number(participant_phone)
        
        # Use GreenAPI's addGroupParticipant method
        response = whatsapp_client.client.groups.addGroupParticipant(
            groupId=group_id,
            participantChatId=formatted_phone
        )

        logger.info(f"Add participant response code: {response.code}")
        logger.info(f"Add participant response: {response.data}")

        if response.code == 200:
            logger.info(f"Successfully added {formatted_phone} to group {group_id}")
            return True
        else:
            logger.error(f"Failed to add participant. Response code: {response.code}, Data: {response.data}")
            return False

    except Exception as e:
        logger.error(f"Failed to add participant {participant_phone} to group {group_id}: {e}")
        return False


async def remove_participant_from_group(group_id: str, participant_phone: str) -> bool:
    """Remove a participant from a WhatsApp group using GreenAPI."""
    logger.info(f"Removing participant {participant_phone} from group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        formatted_phone = _format_phone_number(participant_phone)
        
        # Use GreenAPI's removeGroupParticipant method
        response = whatsapp_client.client.groups.removeGroupParticipant(
            groupId=group_id,
            participantChatId=formatted_phone
        )

        logger.info(f"Remove participant response code: {response.code}")
        logger.info(f"Remove participant response: {response.data}")

        if response.code == 200:
            logger.info(f"Successfully removed {formatted_phone} from group {group_id}")
            return True
        else:
            logger.error(f"Failed to remove participant. Response code: {response.code}, Data: {response.data}")
            return False

    except Exception as e:
        logger.error(f"Failed to remove participant {participant_phone} from group {group_id}: {e}")
        return False


async def leave_group(group_id: str) -> bool:
    """Leave a WhatsApp group using GreenAPI."""
    logger.info(f"Leaving group {group_id}")

    whatsapp_client = auth_manager.get_client()
    if not whatsapp_client:
        raise ValueError("Session not found")

    if not whatsapp_client.client:
        raise ValueError("WhatsApp client not initialized")

    try:
        # Use GreenAPI's leaveGroup method
        response = whatsapp_client.client.groups.leaveGroup(group_id)

        logger.info(f"Leave group response code: {response.code}")
        logger.info(f"Leave group response: {response.data}")

        if response.code == 200:
            logger.info(f"Successfully left group {group_id}")
            return True
        else:
            logger.error(f"Failed to leave group. Response code: {response.code}, Data: {response.data}")
            return False

    except Exception as e:
        logger.error(f"Failed to leave group {group_id}: {e}")
        return False
