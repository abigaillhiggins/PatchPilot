from openai import OpenAI
import os
import re

def validate_api_key_format(api_key: str) -> tuple[bool, str]:
    """Validate the format of an OpenAI API key.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not api_key:
        return False, "API key is empty"
    
    # Check for either standard or project-specific API key format
    if not (api_key.startswith('sk-') or api_key.startswith('sk-proj-')):
        return False, "API key must start with 'sk-' or 'sk-proj-'"
    
    if len(api_key) < 40:  # OpenAI keys are typically longer than this
        return False, "API key appears too short"
        
    # Allow more characters for project keys
    if not re.match(r'^sk-(?:proj-)?[A-Za-z0-9_-]+$', api_key):
        return False, "API key contains invalid characters"
    
    return True, ""

def test_openai_api_key(api_key: str = None) -> tuple[bool, str]:
    """Test if the OpenAI API key is valid by making a simple API call.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    print("\n=== Testing OpenAI API Key ===")
    
    # Use provided key or environment variable
    key_to_test = api_key or os.getenv('OPENAI_API_KEY')
    if not key_to_test:
        error_msg = """
Error: No API key provided. To fix this:
1. Get your API key from https://platform.openai.com/api-keys
2. Set it as an environment variable:
   export OPENAI_API_KEY='your-key-here'
"""
        print(error_msg)
        return False, "No API key provided"

    # Validate key format first
    is_valid_format, format_error = validate_api_key_format(key_to_test)
    if not is_valid_format:
        print(f"\nError: Invalid API key format - {format_error}")
        return False, f"Invalid format: {format_error}"
        
    print(f"Testing API key: {key_to_test[:8]}...{key_to_test[-4:]}")
    
    try:
        # Initialize the client
        client = OpenAI(api_key=key_to_test)
        
        # Make a simple API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using 3.5-turbo as it's more widely available
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
        if "Incorrect API key provided" in error_msg:
            print("\nThe API key format is correct but the key is invalid or revoked.")
            print("Please check your API key at: https://platform.openai.com/api-keys")
        elif "Rate limit" in error_msg:
            print("\nRate limit hit. Your API key is valid but you've hit your usage limits.")
        elif "insufficient_quota" in error_msg:
            print("\nYour API key is valid but you have insufficient quota.")
            print("Please check your usage at: https://platform.openai.com/usage")
            
        return False, f"API error: {error_msg}"

def main():
    """Main function to test the API key."""
    # Get the current API key
    current_key = os.getenv('OPENAI_API_KEY')
    
    # Test the key
    success, message = test_openai_api_key(current_key)
    
    # Exit with appropriate status code
    exit(0 if success else 1)

if __name__ == "__main__":
    main() 