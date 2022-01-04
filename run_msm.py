import os
import requests
import json


#runs MSM_Better
exec(open("./model_minerals/MSM_Better_Two_Degree.py").read())

#APi call to API wrapper
response = requests.post("https://wrapapi.com/use/mtanner16/powerbi/refreshBetter/latest", json={
  "wrapAPIKey": "5qFgLhXFUJpNLypp50lh6YLEPbC7NmgE"
})

response.json()

print("Done")