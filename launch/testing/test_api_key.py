import groq
import os
import re
from typing import Tuple
import sys

def validate_api_key_format(key: str) -> tuple[bool, str]:
    """Validate the format of a Groq API key.
    
    Args:
        key: The API key to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not key:
        return False, "API key is empty"
        
    if not key.startswith('gsk_'):
        return False, "API key must start with 'gsk_'"
        
    if len(key) < 40:
        return False, "API key must be at least 40 characters long"
        
    return True, "API key format is valid"

def test_groq_api_key(key_to_test: str) -> tuple[bool, str]:
    """Test if a Groq API key is valid and working.
    
    Args:
        key_to_test: The API key to test
        
    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    if not key_to_test:
        return False, "No API key provided"
        
    # First validate the format
    is_valid, error = validate_api_key_format(key_to_test)
    if not is_valid:
        return False, error
        
    print(f"Testing API key: {key_to_test[:8]}...{key_to_test[-4:]}")
    
    try:
        # Initialize the client
        client = groq.Groq(api_key=key_to_test)
        
        # Make a simple API call
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",  # Using Qwen3-32B for testing
            messages=[
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Say 'API key is valid' if you receive this message."}
            ],
            max_tokens=10
        )
        
        # Check response
        if response and response.choices:
            print("\nAPI Response:")
            print(response.choices[0].message.content)
            print("\nAPI key is valid and working!")
            return True, "API key is valid"
            
    except Exception as e:
        error_msg = str(e)
        print("\nError testing API key:")
        print(error_msg)
        
        # Provide more helpful messages for common errors
        if "invalid_api_key" in error_msg:
            print("\nThe API key format is correct but the key is invalid or revoked.")
            print("Please check your API key at: https://console.groq.com/keys")
        elif "rate_limit" in error_msg:
            print("\nRate limit hit. Your API key is valid but you've hit your usage limits.")
        elif "quota" in error_msg:
            print("\nYour API key is valid but you have insufficient quota.")
            print("Please check your usage at: https://console.groq.com/usage")
            
        return False, f"API error: {error_msg}"

def main():
    """Main function to test the API key."""
    # Get the current API key
    current_key = os.getenv('GROQ_API_KEY')
    
    # Test the key
    success, message = test_groq_api_key(current_key)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 