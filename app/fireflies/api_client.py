"""
Fireflies API Client - Clean GraphQL client for Fireflies.ai API
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class FirefliesAPIClient:
    """
    Clean Fireflies API client for making GraphQL requests
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FIREFLIES_API_KEY')
        self.base_url = "https://api.fireflies.ai/graphql"
        
        if not self.api_key:
            raise ValueError("FIREFLIES_API_KEY is required. Provide it as a parameter.")
    
    def _make_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to the Fireflies API
        
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
        
        data = {'query': query}
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
        Test if the API connection and key are working
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            query = "{ users { name user_id } }"
            result = self._make_request(query)
            return "data" in result and "users" in result["data"]
        except Exception:
            return False