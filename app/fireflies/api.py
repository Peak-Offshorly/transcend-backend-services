import requests
from typing import Dict, Any, Optional
from app.const import FIREFLIES_API_KEY


class FirefliesAPI:
    """
    Base Fireflies API client for making GraphQL requests
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or FIREFLIES_API_KEY
        self.base_url = "https://api.fireflies.ai/graphql"
        
        if not self.api_key:
            raise ValueError("FIREFLIES_API_KEY is required. Set it in your .env file.")
    
    def _make_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to the Fireflies API (using official docs format)
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the API returns an error
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'query': query
        }
        
        # Add variables if provided
        if variables:
            data['variables'] = variables
        
        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error_messages = [error.get("message", "Unknown error") for error in result["errors"]]
                raise ValueError(f"GraphQL errors: {', '.join(error_messages)}")
                
            return result
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Fireflies API request failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test if the API connection and key are working (using docs example)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Use the exact query from Fireflies docs
            query = "{ users { name user_id } }"
            result = self._make_request(query)
            return "data" in result and "users" in result["data"]
        except Exception:
            return False