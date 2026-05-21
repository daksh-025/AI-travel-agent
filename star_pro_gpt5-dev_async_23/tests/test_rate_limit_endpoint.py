"""
Quick test to verify the rate limit endpoint works without authentication.
Run this to test the 403 bug fix.
"""
import requests

BASE_URL = "http://localhost:8000"

def test_rate_limit_endpoint():
    print("=" * 60)
    print("Testing /chat/rate-limit endpoint (no auth)")
    print("=" * 60)
    print()
    
    try:
        # Test without authentication (should return 200, not 403)
        print("1. Testing WITHOUT authentication...")
        response = requests.get(f"{BASE_URL}/chat/rate-limit")
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS - Endpoint works without auth!")
            data = response.json()
            print(f"   Response: {data}")
        elif response.status_code == 403:
            print("   ❌ FAILED - Still getting 403 Forbidden")
            print("   This means the fix didn't work properly.")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print()
        
        # Test with invalid token (should return 200 with guest info)
        print("2. Testing WITH invalid token...")
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{BASE_URL}/chat/rate-limit", headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS - Endpoint handles invalid token gracefully!")
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print()
        print("=" * 60)
        print("Test Complete!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API")
        print("Make sure the server is running:")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_rate_limit_endpoint()

