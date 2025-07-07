"""Models for WhatsApp MCP Server."""

from enum import Enum
from typing import Any, Dict, List, Union, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class CreateSessionModel(BaseModel):
    """Input schema for open_session tool."""
    pass


class GetChatsModel(BaseModel):
    """Input schema for get_chats tool."""
    limit: int = Field(50, description="Maximum number of chats to return")
    offset: int = Field(0, description="Offset for pagination")


class MCP_MessageType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"


class TextContent(BaseModel):
    """Text content for messages."""
    type: str = "text"
    text: str


class Contact(BaseModel):
    """WhatsApp contact model."""
    id: str = Field(..., description="Contact ID (phone number)")
    name: Optional[str] = Field(None, description="Contact name")
    phone: Optional[str] = Field(None, description="Phone number")
    is_business: bool = Field(False, description="Whether this is a business contact")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")


class Participant(BaseModel):
    """WhatsApp group participant model."""
    id: str = Field(..., description="Participant ID (phone number)")
    name: Optional[str] = Field(None, description="Participant name")
    role: str = Field("member", description="Participant role (admin, member)")
    is_admin: bool = Field(False, description="Whether participant is admin")
    joined_at: Optional[str] = Field(None, description="When participant joined")


class Group(BaseModel):
    """WhatsApp group model."""
    id: str = Field(..., description="Group ID")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    participants: List[Participant] = Field(default_factory=list, description="Group participants")
    created_at: Optional[str] = Field(None, description="Group creation timestamp")
    created_by: Optional[str] = Field(None, description="Group creator")
    is_announcement: bool = Field(False, description="Whether group is announcement only")
    invite_link: Optional[str] = Field(None, description="Group invite link")
    error: Optional[str] = Field(None, description="Error message if group creation failed")


class Message(BaseModel):
    """WhatsApp message model."""
    id: str = Field(..., description="Message ID")
    chat_id: str = Field(..., description="Chat ID where message was sent")
    sender_id: Optional[str] = Field(None, description="Sender ID")
    content: str = Field(..., description="Message content")
    message_type: str = Field("text", description="Message type")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    reply_to: Optional[str] = Field(None, description="ID of message being replied to")
    status: str = Field("sent", description="Message status")


class Chat(BaseModel):
    """WhatsApp chat model."""
    id: str = Field(..., description="Chat ID")
    name: Optional[str] = Field(None, description="Chat name")
    type: str = Field("contact", description="Chat type (contact, group)")
    last_message: Optional[str] = Field(None, description="Last message content")
    last_message_time: Optional[str] = Field(None, description="Last message timestamp")
    unread_count: int = Field(0, description="Number of unread messages")
    is_archived: bool = Field(False, description="Whether chat is archived")
    is_pinned: bool = Field(False, description="Whether chat is pinned")


class SessionStatus(BaseModel):
    """WhatsApp session status model."""
    authenticated: bool = Field(False, description="Whether session is authenticated")
    state: str = Field("disconnected", description="Session state")
    message: str = Field("", description="Status message")
    instance_id: Optional[str] = Field(None, description="WhatsApp instance ID")
    phone_number: Optional[str] = Field(None, description="Associated phone number")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class AccountInfo(BaseModel):
    """WhatsApp account information model."""
    phone_number: Optional[str] = Field(None, description="Account phone number")
    name: Optional[str] = Field(None, description="Account name")
    status: Optional[str] = Field(None, description="Account status")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    is_business: bool = Field(False, description="Whether this is a business account")
    settings: Optional[Dict[str, Any]] = Field(None, description="Account settings")
    state: Optional[Dict[str, Any]] = Field(None, description="Account state")
    authenticated: bool = Field(False, description="Whether account is authenticated")
    retrieved_at: Optional[str] = Field(None, description="When info was retrieved")
