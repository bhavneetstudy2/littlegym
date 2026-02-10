"""Add Chandigarh center."""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@thelittlegym.in",
    "password": "admin123"
})
data = login_response.json()
token = data["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create Chandigarh center
response = requests.post(f"{BASE_URL}/centers", json={
    "name": "The Little Gym - Chandigarh",
    "city": "Chandigarh",
    "timezone": "Asia/Kolkata",
    "address": "Sector 17, Chandigarh 160017",
    "phone": "+91 172 2700000"
}, headers=headers)

if response.status_code == 200:
    c = response.json()
    print(f"Created: {c['id']}: {c['name']}")
else:
    print(f"Result: {response.text}")

# List all centers
print("\nAll centers:")
centers_response = requests.get(f"{BASE_URL}/centers", headers=headers)
for c in centers_response.json():
    print(f"  - {c['id']}: {c['name']} ({c['city']})")
