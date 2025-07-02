#!/usr/bin/env python3
"""
Fireflies API Test Script

Run this script to test your Fireflies API integration and key.
"""

import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fireflies.users import test_connection, get_user_info, get_user_integrations


def print_separator(title: str):
    """Print a nice separator with title"""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)


def test_api_key():
    """Test the Fireflies API key and connection"""
    print_separator("FIREFLIES API CONNECTION TEST")
    
    try:
        # Test basic connection
        result = test_connection()
        
        if result["connected"]:
            print("✅ SUCCESS: Connected to Fireflies API!")
            print(f"📧 Email: {result['user_data']['email']}")
            print(f"👤 Name: {result['user_data']['name']}")
            print(f"⏱️  Meeting Minutes Remaining: {result['user_data']['meeting_minutes_remaining']}")
            print(f"📋 Plan: {result['user_data']['plan_name']}")
            print(f"🔗 Integrations: {result['user_data']['integrations_count']}")
            
            return True
        else:
            print("❌ FAILED: Could not connect to Fireflies API")
            print(f"Error: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def test_user_info():
    """Test getting detailed user information"""
    print_separator("DETAILED USER INFORMATION")
    
    try:
        user_info = get_user_info()
        
        if user_info:
            print(f"User ID: {user_info.get('user_id', 'N/A')}")
            print(f"Email: {user_info.get('email', 'N/A')}")
            print(f"Name: {user_info.get('name', 'N/A')}")
            
            # Plan details
            plan = user_info.get('plan', {})
            if plan:
                print(f"\nPlan Information:")
                print(f"  - Plan Name: {plan.get('name', 'N/A')}")
                print(f"  - Max Meeting Minutes: {plan.get('max_meeting_minutes', 'N/A')}")
                print(f"  - Max Storage Minutes: {plan.get('max_storage_minutes', 'N/A')}")
            
            print(f"Meeting Minutes Remaining: {user_info.get('meeting_minutes_remaining', 'N/A')}")
            
            return True
        else:
            print("❌ No user information returned")
            return False
            
    except Exception as e:
        print(f"❌ ERROR getting user info: {str(e)}")
        return False


def test_integrations():
    """Test getting user integrations"""
    print_separator("USER INTEGRATIONS")
    
    try:
        integrations = get_user_integrations()
        
        if integrations:
            print(f"Found {len(integrations)} integration(s):")
            for i, integration in enumerate(integrations, 1):
                print(f"\n{i}. {integration.get('name', 'Unknown')}")
                print(f"   Status: {integration.get('status', 'Unknown')}")
                print(f"   Connected: {integration.get('connected_at', 'Unknown')}")
                
                settings = integration.get('settings', {})
                if settings:
                    print(f"   Auto-join: {settings.get('auto_join_meetings', 'N/A')}")
                    print(f"   Auto-record: {settings.get('record_meetings', 'N/A')}")
        else:
            print("No integrations found or user has no connected services")
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR getting integrations: {str(e)}")
        return False


def main():
    """Main test function"""
    print("FIREFLIES API TESTING")
    print("Testing Fireflies API integration...")
    
    # Test 1: Basic connection
    connection_success = test_api_key()
    
    if not connection_success:
        print("\n❌ OVERALL RESULT: API key test failed!")
        print("\nTroubleshooting:")
        print("1. Check that FIREFLIES_API_KEY is set in your .env file")
        print("2. Verify your API key is correct in your Fireflies dashboard")
        print("3. Ensure your Fireflies account has API access")
        return
    
    # Test 2: Detailed user info
    user_info_success = test_user_info()
    
    # Test 3: Integrations
    integrations_success = test_integrations()
    
    # Summary
    print_separator("TEST SUMMARY")
    print(f"✅ Connection Test: {'PASSED' if connection_success else 'FAILED'}")
    print(f"✅ User Info Test: {'PASSED' if user_info_success else 'FAILED'}")
    print(f"✅ Integrations Test: {'PASSED' if integrations_success else 'FAILED'}")
    
    if all([connection_success, user_info_success, integrations_success]):
        print("\n🎉 ALL TESTS PASSED! Your Fireflies API integration is working correctly.")
        print("\nNext steps:")
        print("- You can now build more advanced Fireflies functionality")
        print("- Consider adding transcript fetching, meeting management, etc.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above for details.")


if __name__ == "__main__":
    main()