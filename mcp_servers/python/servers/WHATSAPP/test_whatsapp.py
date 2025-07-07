#!/usr/bin/env python3
"""Test script to verify WhatsApp GreenAPI credentials and phone number format."""

import sys
import requests
import json

def test_greenapi_credentials(id_instance, api_token):
    """Test GreenAPI credentials by getting account settings."""
    print("🔍 Testing GreenAPI credentials...")
    
    url = f"https://api.green-api.com/waInstance{id_instance}/getSettings/{api_token}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Credentials are valid!")
            print(f"📋 Account Settings: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Invalid credentials. Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

def test_instance_state(id_instance, api_token):
    """Test instance state."""
    print("\n🔍 Testing instance state...")
    
    url = f"https://api.green-api.com/waInstance{id_instance}/getStateInstance/{api_token}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            state = data.get("stateInstance", "unknown")
            print(f"📱 Instance State: {state}")
            
            if state == "authorized":
                print("✅ Instance is authorized and ready!")
                return True
            elif state == "notAuthorized":
                print("⚠️  Instance is not authorized. Please scan QR code in your GreenAPI console.")
                return False
            else:
                print(f"⚠️  Instance state: {state}")
                return False
        else:
            print(f"❌ Error getting state. Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing state: {e}")
        return False

def test_send_message(id_instance, api_token, phone_number, message):
    """Test sending a message."""
    print(f"\n🔍 Testing message sending to {phone_number}...")
    
    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
    
    payload = {
        "chatId": phone_number,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Message sent successfully!")
            print(f"📋 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Failed to send message. Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def validate_phone_number(phone_number):
    """Validate phone number format."""
    print(f"\n🔍 Validating phone number format: {phone_number}")
    
    if not phone_number.endswith("@c.us"):
        print("❌ Phone number should end with @c.us")
        return False
    
    number_part = phone_number.replace("@c.us", "")
    
    if not number_part.isdigit():
        print("❌ Phone number should contain only digits before @c.us")
        return False
    
    if len(number_part) < 10:
        print("❌ Phone number seems too short")
        return False
    
    if number_part.startswith("91") and len(number_part) == 12:
        print("✅ Valid Indian phone number format")
        return True
    elif len(number_part) >= 10:
        print("✅ Valid international phone number format")
        return True
    else:
        print("⚠️  Phone number format may be incorrect")
        return False

def main():
    """Main test function."""
    print("🚀 WhatsApp GreenAPI Test Script")
    print("=" * 50)
    
    # Your credentials from the request
    id_instance = "7105277568"
    api_token = "19392399b3984fac830f14d42d54dd70d990628b0c5c422fa0"
    phone_number = "918411911659@c.us"
    test_message = "Hello! This is a test message from WhatsApp MCP Server. How are you today?"
    
    print(f"🔑 ID Instance: {id_instance}")
    print(f"🔑 API Token: {api_token[:20]}...")
    print(f"📱 Phone Number: {phone_number}")
    
    # Step 1: Validate phone number format
    if not validate_phone_number(phone_number):
        print("\n❌ Phone number validation failed!")
        return
    
    # Step 2: Test credentials
    if not test_greenapi_credentials(id_instance, api_token):
        print("\n❌ Credential test failed!")
        return
    
    # Step 3: Test instance state
    if not test_instance_state(id_instance, api_token):
        print("\n❌ Instance state test failed!")
        return
    
    # Step 4: Test message sending
    print(f"\n🚀 All tests passed! Attempting to send test message...")
    if test_send_message(id_instance, api_token, phone_number, test_message):
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Message sending failed!")

if __name__ == "__main__":
    main()
