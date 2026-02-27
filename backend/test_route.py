import requests

url_base = "https://sga-h-api-377936686920.us-central1.run.app"
headers = {"Origin": "https://sga-escola-app.vercel.app"}

print("--- Testing POST /api/assessments/batch directly (Empty Payload) ---")
res = requests.post(f"{url_base}/api/assessments/batch", json=[], headers=headers)
print(res.status_code, res.text)

print("--- Testing OPTIONS /api/assessments/batch ---")
res2 = requests.options(f"{url_base}/api/assessments/batch", headers={
    "Origin": "https://sga-escola-app.vercel.app",
    "Access-Control-Request-Method": "POST"
})
print(res2.status_code, res2.headers)
