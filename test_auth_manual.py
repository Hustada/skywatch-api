"""Manual test script for API key authentication system."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("🧪 Testing SkyWatch API Authentication System\n")
    
    # Test 1: Public endpoint (should work without API key)
    print("1. Testing public health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health endpoint accessible without API key")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print()
    
    # Test 2: Protected endpoint without API key (should fail)
    print("2. Testing protected sightings endpoint without API key...")
    try:
        response = requests.get(f"{BASE_URL}/v1/sightings")
        if response.status_code == 401:
            print("✅ Sightings endpoint correctly rejects requests without API key")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Sightings endpoint error: {e}")
    
    print()
    
    # Test 3: User registration
    print("3. Testing user registration...")
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/v1/auth/register", json=user_data)
        if response.status_code == 200:
            print("✅ User registration successful")
            user_info = response.json()
            print(f"   User ID: {user_info['id']}")
            print(f"   Name: {user_info['name']}")
            print(f"   Email: {user_info['email']}")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ User already exists (from previous test run)")
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ User registration error: {e}")
    
    print()
    
    # Test 4: User login
    print("4. Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    access_token = None
    try:
        response = requests.post(f"{BASE_URL}/v1/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ User login successful")
            token_data = response.json()
            access_token = token_data['access_token']
            print(f"   Token type: {token_data['token_type']}")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print(f"❌ User login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ User login error: {e}")
    
    print()
    
    # Test 5: Create API key
    if access_token:
        print("5. Testing API key creation...")
        headers = {"Authorization": f"Bearer {access_token}"}
        api_key_data = {
            "name": "Test API Key",
            "tier": "free"
        }
        
        api_key = None
        try:
            response = requests.post(f"{BASE_URL}/v1/auth/keys", json=api_key_data, headers=headers)
            if response.status_code == 200:
                print("✅ API key creation successful")
                key_response = response.json()
                api_key = key_response['api_key']
                print(f"   API Key: {api_key}")  # Show full key for testing
                print(f"   Key Name: {key_response['key_info']['name']}")
                print(f"   Tier: {key_response['key_info']['tier']}")
                print(f"   Quota Limit: {key_response['key_info']['quota_limit']}")
            else:
                print(f"❌ API key creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ API key creation error: {e}")
        
        print()
        
        # Test 6: Use API key to access protected endpoint
        if api_key:
            print("6. Testing protected endpoint with API key...")
            headers = {"X-API-Key": api_key}
            
            try:
                response = requests.get(f"{BASE_URL}/v1/sightings", headers=headers)
                if response.status_code == 200:
                    print("✅ Sightings endpoint accessible with API key")
                    data = response.json()
                    print(f"   Total sightings: {data['total']}")
                    print(f"   Page: {data['page']}")
                    print(f"   Sightings returned: {len(data['sightings'])}")
                else:
                    print(f"❌ Sightings endpoint failed with API key: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Sightings endpoint with API key error: {e}")
            
            print()
            
            # Test 7: Check usage stats (using API key, not JWT token)
            print("7. Testing usage statistics...")
            api_key_headers = {"X-API-Key": api_key}
            try:
                response = requests.get(f"{BASE_URL}/v1/auth/usage", headers=api_key_headers)
                if response.status_code == 200:
                    print("✅ Usage statistics accessible")
                    usage = response.json()
                    print(f"   Total requests: {usage['total_requests']}")
                    print(f"   Requests this month: {usage['requests_this_month']}")
                    print(f"   Quota used: {usage['quota_used']}/{usage['quota_limit']}")
                    print(f"   Quota remaining: {usage['quota_remaining']}")
                else:
                    print(f"❌ Usage statistics failed: {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ Usage statistics error: {e}")
    
    print("\n🎉 API Key Authentication System Test Complete!")

if __name__ == "__main__":
    test_endpoints()