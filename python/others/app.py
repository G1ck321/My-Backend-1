from member import name
from twilio.rest import Client
from pprint import pprint
print(name)
client = Client("ACe3f34e847ee786230a7f279a9d29373f","856be243f6ef926ac7a02c7e7949b1dd")

message = client.messages.create(
    from_="+19492673112",
    body=name,
    to="+08020713273")

print(message.sid)