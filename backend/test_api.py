"""Test API and add centers if needed."""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("Logging in...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "admin@thelittlegym.in",
    "password": "admin123"
})

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

data = login_response.json()
token = data["access_token"]
print(f"Logged in as: {data['user']['name']}")

# Get headers
headers = {"Authorization": f"Bearer {token}"}

# Check centers
print("\nFetching centers...")
centers_response = requests.get(f"{BASE_URL}/centers", headers=headers)
centers = centers_response.json()
print(f"Found {len(centers)} centers:")
for c in centers:
    print(f"  - {c['id']}: {c['name']} ({c['city']})")

# If no centers, create them
if len(centers) == 0:
    print("\nNo centers found. Creating centers...")

    centers_to_create = [
        {
            "name": "The Little Gym - Mumbai Central",
            "city": "Mumbai",
            "timezone": "Asia/Kolkata",
            "address": "123 Main Street, Mumbai, Maharashtra 400001",
            "phone": "+91 22 1234 5678"
        },
        {
            "name": "The Little Gym - Delhi North",
            "city": "Delhi",
            "timezone": "Asia/Kolkata",
            "address": "456 Park Road, Delhi 110001",
            "phone": "+91 11 9876 5432"
        },
        {
            "name": "The Little Gym - Chandigarh",
            "city": "Chandigarh",
            "timezone": "Asia/Kolkata",
            "address": "Sector 17, Chandigarh 160017",
            "phone": "+91 172 2700000"
        }
    ]

    for center_data in centers_to_create:
        response = requests.post(f"{BASE_URL}/centers", json=center_data, headers=headers)
        if response.status_code == 200:
            c = response.json()
            print(f"  Created: {c['id']}: {c['name']}")
        else:
            print(f"  Failed to create {center_data['name']}: {response.text}")

print("\nDone!")
