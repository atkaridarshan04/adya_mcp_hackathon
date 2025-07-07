#!/usr/bin/env python3
"""Test phone number formatting for WhatsApp."""

def _get_chat_id(phone_number: str) -> str:
    """Get the chat ID for a phone number."""
    # Remove the country code symbol and clean the number
    phone_number = phone_number.strip().replace("+", "")
    
    # If the number already has @c.us suffix, extract the number part
    if phone_number.endswith("@c.us"):
        number_part = phone_number.replace("@c.us", "")
    else:
        number_part = phone_number
    
    # Ensure the number is in the correct format for GreenAPI
    # For Indian numbers, GreenAPI expects format: 91XXXXXXXXXX@c.us
    if number_part.isdigit():
        # If it's an Indian number starting with 91, keep as is
        if number_part.startswith("91") and len(number_part) == 12:
            return f"{number_part}@c.us"
        # If it's a 10-digit Indian number, add 91 prefix
        elif len(number_part) == 10 and not number_part.startswith("91"):
            return f"91{number_part}@c.us"
        # For other international numbers, keep as is
        else:
            return f"{number_part}@c.us"
    
    # If already formatted correctly, return as is
    return phone_number if phone_number.endswith("@c.us") else f"{phone_number}@c.us"

def test_phone_formats():
    """Test various phone number formats."""
    test_cases = [
        "918411911659@c.us",
        "918411911659",
        "8411911659",
        "+918411911659",
        "91 8411911659",
        "8411911659@c.us"
    ]
    
    print("🧪 Testing phone number formats:")
    print("=" * 50)
    
    for phone in test_cases:
        formatted = _get_chat_id(phone)
        print(f"Input:  '{phone}'")
        print(f"Output: '{formatted}'")
        print("-" * 30)

if __name__ == "__main__":
    test_phone_formats()
