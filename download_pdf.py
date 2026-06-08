import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzc5Nzc1MzYzfQ.oEjl2aNl3DM-C2c8NkazrgJIraWSbrYXE6oJs4_6NJ0"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/pdf"}
response = requests.post("http://localhost:8000/rao/api/reports/contract/15458?type=contract", headers=headers)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")

with open("contract_15458.pdf", "wb") as f:
    f.write(response.content)

print(f"Downloaded {len(response.content)} bytes")