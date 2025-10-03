"""
Fireflies API Client - Clean GraphQL client for Fireflies.ai API
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def format_wait_time(seconds: int) -> str:
    """
    Convert seconds to human-readable time format

    Args:
        seconds: Number of seconds to wait

    Returns:
        Human-readable time string (e.g., "1 hour and 27 minutes", "5 minutes", "45 seconds")
    """
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"


class FirefliesError(Exception):
    """Custom exception for Fireflies API errors"""
    def __init__(self, code: str, message: str, retry_after: Optional[int] = None):
        self.code = code
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class FirefliesAPIClient:
    """
    Clean Fireflies API client for making GraphQL requests
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FIREFLIES_API_KEY')
        self.base_url = "https://api.fireflies.ai/graphql"

        if not self.api_key:
            raise ValueError("FIREFLIES_API_KEY is required. Provide it as a parameter.")

    @staticmethod
    def parse_graphql_error(error: Dict[str, Any]) -> FirefliesError:
        """
        Parse Fireflies GraphQL error and return structured error

        Args:
            error: GraphQL error dictionary

        Returns:
            FirefliesError with code, message, and retry_after if applicable
        """
        error_message = error.get("message", "Unknown error")

        # Extract error code from extensions if available
        extensions = error.get("extensions", {})
        error_code_from_ext = extensions.get("code", "")

        # Map common Fireflies error codes to user-friendly messages
        error_mappings = {
            "invalid_arguments": ("invalid_arguments", "Invalid arguments provided. Please check your request."),
            "object_not_found": ("object_not_found", "The requested object was not found."),
            "forbidden": ("forbidden", "Access denied. Please check your API token permissions."),
            "paid_required": ("paid_required", "This feature requires a paid Fireflies subscription."),
            "not_in_team": ("not_in_team", "The requested user is not in your team."),
            "require_elevated_privilege": ("require_elevated_privilege", "Admin privileges required for this action."),
            "account_cancelled": ("account_cancelled", "Your Fireflies account is inactive. Please check your subscription."),
            "args_required": ("args_required", "Missing required arguments in the request."),
            "too_many_requests": ("too_many_requests", "Rate limit exceeded. Please try again later."),
            "payload_too_small": ("payload_too_small", "Upload content is too small (minimum 50kb required)."),
            "request_timeout": ("request_timeout", "Request timed out. Your data may still be processing."),
            "invalid_language_code": ("invalid_language_code", "Unsupported or invalid language code."),
            "admin_must_exist": ("admin_must_exist", "Cannot remove the last admin from the team."),
            "unsupported_platform": ("unsupported_platform", "Invalid meeting platform URL."),
            "invariant_violation": ("invariant_violation", "An unexpected error occurred. Please try again."),
        }

        # Check error code from extensions first, then fall back to message parsing
        matched_code = None
        if error_code_from_ext in error_mappings:
            matched_code = error_code_from_ext
        else:
            # Fall back to checking if error code is in the message
            for error_code in error_mappings.keys():
                if error_code in error_message.lower():
                    matched_code = error_code
                    break

        if matched_code:
            code, friendly_msg = error_mappings[matched_code]

            # Extract retry_after for rate limiting from extensions.metadata.retryAfter
            retry_after = None
            if matched_code == "too_many_requests":
                metadata = extensions.get("metadata", {})
                retry_after_ms = metadata.get("retryAfter")
                if retry_after_ms:
                    # Convert milliseconds timestamp to seconds from now
                    import time
                    current_time_ms = int(time.time() * 1000)
                    retry_after = max(0, int((retry_after_ms - current_time_ms) / 1000))
                    # Update friendly message with human-readable time
                    if retry_after > 0:
                        friendly_msg = f"Rate limit exceeded. Please try again in {format_wait_time(retry_after)}."

            return FirefliesError(code, friendly_msg, retry_after)

        # Default error if no specific code matched
        return FirefliesError("unknown_error", error_message)
    
    def _make_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GraphQL request to the Fireflies API

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Dict containing the API response

        Raises:
            FirefliesError: If the API returns a known error code
            requests.RequestException: If the API request fails
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        data = {'query': query}
        if variables:
            data['variables'] = variables

        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=60)

            # Handle HTTP error status codes
            if response.status_code == 401:
                raise FirefliesError("unauthorized", "Invalid or expired API token.")
            elif response.status_code == 403:
                raise FirefliesError("forbidden", "Access denied. Please check your API token permissions.")
            elif response.status_code == 404:
                raise FirefliesError("object_not_found", "The requested resource was not found.")
            elif response.status_code == 408:
                raise FirefliesError("request_timeout", "Request timed out. Your data may still be processing.")
            elif response.status_code == 429:
                # Extract retry-after header if present
                retry_after = response.headers.get('Retry-After')
                retry_seconds = int(retry_after) if retry_after else None
                # Create human-readable message if retry time is available
                if retry_seconds:
                    friendly_msg = f"Rate limit exceeded. Please try again in {format_wait_time(retry_seconds)}."
                else:
                    friendly_msg = "Rate limit exceeded. Please try again later."
                raise FirefliesError("too_many_requests", friendly_msg, retry_seconds)

            # Check for success status codes before processing
            if response.status_code >= 500:
                # Check if 500 error is due to authentication issues
                response_body = response.text.lower()
                auth_keywords = [
                    "unauthorized", "invalid token", "forbidden", "authentication", "authenticating",
                    "invalid api key", "access denied", "invalid_api_key", "unauthenticated",
                    "auth_failed", "auth failed"
                ]

                if any(keyword in response_body for keyword in auth_keywords):
                    raise FirefliesError("unauthorized", "Invalid or expired API token.")

                # If not auth-related, let it fall through to raise_for_status below

            # Raise for any other HTTP errors not explicitly handled above
            response.raise_for_status()
            result = response.json()

            # Check for GraphQL errors
            if "errors" in result and len(result["errors"]) > 0:
                # Parse the first error
                first_error = result["errors"][0]
                raise self.parse_graphql_error(first_error)

            return result

        except FirefliesError:
            # Re-raise FirefliesError as-is
            raise
        except requests.RequestException as e:
            # Wrap other request exceptions as generic network error
            raise FirefliesError("network_error", f"Network error occurred: {str(e)}")
    
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