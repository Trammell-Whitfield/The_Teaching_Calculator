#!/usr/bin/env python3
"""
Quick test script to verify Wolfram Alpha API connection
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_wolfram_api():
    """Test basic Wolfram Alpha API connectivity"""

    api_key = os.getenv('WOLFRAM_ALPHA_API_KEY')

    if not api_key or api_key == 'your_api_key_here':
        print("❌ ERROR: API key not set in .env file")
        return False

    print(f"✓ API key loaded: {api_key[:4]}...{api_key[-4:]}")

    # Simple test query
    test_query = "2+2"
    url = f"http://api.wolframalpha.com/v1/result"

    params = {
        'appid': api_key,
        'i': test_query
    }

    print(f"\nTesting query: '{test_query}'")
    print("Sending request to Wolfram Alpha...")

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            print(f"✅ SUCCESS! Response: {response.text}")
            print("\n🎉 Your Wolfram Alpha API is working correctly!")
            return True
        elif response.status_code == 401:
            print(f"❌ AUTHENTICATION ERROR: Invalid API key")
            return False
        elif response.status_code == 403:
            print(f"❌ FORBIDDEN: Check your API key permissions")
            return False
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Holy Calculator - Wolfram Alpha API Test")
    print("=" * 60)
    test_wolfram_api()
