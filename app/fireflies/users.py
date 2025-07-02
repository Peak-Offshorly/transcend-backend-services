from typing import Dict, Any, List
from .api import FirefliesAPI


def get_user_info() -> Dict[str, Any]:
    """
    Get basic user account information (using docs format)
    
    Returns:
        Dict containing user information including:
        - user_id: Unique user identifier
        - email: User's email address
        - name: User's display name
        - integrations: List of connected integrations
        - meeting_minutes_remaining: Available meeting minutes
        - plan: Current subscription plan
    """
    api = FirefliesAPI()
    
    query = "{ users { name user_id email } }"
    
    result = api._make_request(query)
    users_data = result.get("data", {}).get("users", [])
    
    # Return the first user (usually yourself)
    return users_data[0] if users_data else {}


def get_team_members() -> List[Dict[str, Any]]:
    """
    Get list of team members (if using team account)
    
    Returns:
        List of team member dictionaries with their details
    """
    api = FirefliesAPI()
    
    query = """
    query {
        team {
            members {
                user_id
                email
                name
                role
                status
            }
        }
    }
    """
    
    result = api._make_request(query)
    team_data = result.get("data", {}).get("team", {})
    return team_data.get("members", [])


def get_user_integrations() -> List[Dict[str, Any]]:
    """
    Get user's connected calendar and meeting integrations
    
    Returns:
        List of integration dictionaries with name and status
    """
    api = FirefliesAPI()
    
    # Try the corrected query first
    query = """
    {
        users {
            integrations {
                name
                status
                connected_at
                settings {
                    auto_join_meetings
                    record_meetings
                }
            }
        }
    }
    """
    
    try:
        result = api._make_request(query)
        users_data = result.get("data", {}).get("users", [])
        
        # Return integrations from the first user (usually yourself)
        if users_data and len(users_data) > 0:
            return users_data[0].get("integrations", [])
        else:
            return []
            
    except Exception as e:
        # If the above fails, try a simpler query to see what fields are available
        print(f"Detailed integrations query failed: {str(e)}")
        print("Trying simpler query to debug available fields...")
        
        try:
            # Simple query to see all available user fields
            simple_query = "{ users { user_id name email } }"
            result = api._make_request(simple_query)
            users_data = result.get("data", {}).get("users", [])
            
            if users_data:
                print(f"Available user fields: {list(users_data[0].keys())}")
            
            # Return empty list if integrations not available
            return []
            
        except Exception as simple_e:
            print(f"Even simple query failed: {str(simple_e)}")
            return []


def test_connection() -> Dict[str, Any]:
    """
    Test Fireflies API connection and return comprehensive status
    
    Returns:
        Dict with connection status and user information
    """
    try:
        api = FirefliesAPI()
        
        # Test basic connection
        if not api.test_connection():
            return {
                "status": "failed",
                "message": "Unable to connect to Fireflies API",
                "connected": False
            }
        
        # Get user info if connection works
        user_info = get_user_info()
        
        return {
            "status": "success",
            "message": "Successfully connected to Fireflies API",
            "connected": True,
            "user_data": {
                "user_id": user_info.get("user_id"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "meeting_minutes_remaining": user_info.get("meeting_minutes_remaining"),
                "plan_name": user_info.get("plan", {}).get("name"),
                "integrations_count": len(user_info.get("integrations", []))
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "connected": False
        }