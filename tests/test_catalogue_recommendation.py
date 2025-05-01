import requests
import json
from datetime import date, timedelta
import sys
import os

# Add project root to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set base URL
BASE_URL = "http://localhost:8000"  # Change to your API server URL

def test_recommendation_endpoint():
    """Test the catalogue recommendations POST endpoint"""
    
    # Construct the endpoint URL
    url = f"{BASE_URL}/catalogue/recommended-itineraries"
    
    # Create request payload
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "nights": 3,
        "start_date": tomorrow,
        "styles": ["Adventure", "Relaxation"],
        "activities": []  # Optional activities list
    }
    
    # Print request details
    print(f"Making POST request to: {url}")
    print(f"With payload: {json.dumps(payload, indent=2)}")
    
    # Send POST request
    response = requests.post(url, json=payload)
    
    # Print response details
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))
        
        # Basic validation
        assert "message" in result, "Response missing 'message' field"
        assert "itineraries" in result, "Response missing 'itineraries' field"
        return True
    else:
        print(f"Error: {response.text}")
        return False

if __name__ == "__main__":
    test_recommendation_endpoint()
