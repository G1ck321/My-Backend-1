
import requests
import httpx

body_request = {"name":"John"}
# response = requests.post("http://localhost:4000/hi", json=body_request)
# print(response.json())

# resp2 = httpx.post("http://127.0.0.1:4000/hi", json=body_request)
# print(resp2.text)

body_request2 = {"boot":"Boot Camp"}
# resp3 = httpx.post("http://127.0.0.1:6000/ri", json=body_request2)
# print(resp3.text)
# response4 = requests.get("http://localhost:4000/agent")
# print(response4.text)

# response5 = httpx.get("http://localhost:4000/agent")
# print(response5.text)
# returns the usser-Agent

# "python-requests/2.32.5"
# "python-httpx/0.28.1" in this case
bodi = {"tag":"This is my second tag","secret":"opp"}
test_sq = httpx.post( "http://127.0.0.1:8000?secret=opp", json=bodi)
