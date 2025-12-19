import time, sys

# MY = 60
# def timer():
#     global MY
#     none = MY-1
#     time.sleep(1)
#     print(none)
#     MY = none
#     if MY<0:
#         sys.exit(1)
#     timer()
# timer()
import requests
pay = {"firstName":"Jamyes","lastName":"Pauso","email":"gff@mm.xox"}
URL = "http://127.0.0.1:3001/api/students"
response = requests.get(URL)
print(response)
print(response.text)