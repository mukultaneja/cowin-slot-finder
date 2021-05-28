# cowin-slot-finder

A tool to find available vaccination slots for covid vaccine using Co-WIN [public](https://apisetu.gov.in/public/api/cowin) APIs.

`slotFinder.py` is a python script that helps to search available slots using pincodes and districts. It is a continous, automated and, multi-processing based script that can take multiple pincodes and districts to find slots at a time and smart enough to manage time difference between multiple requests to the server. The intention is to never cross `100 requests in 5 mins` boundary imposed by the Co-Win public APIs.

This script is capable enough to filter & send requests to find district-wise slots/pincode-wise slots based on provided data points. Once you start the script, it keeps polling the slots and starts notifying as soon as once available for you.

# Requirements

1. Python 3

# Python Packages

1. requests
2. beepy
3. plyer 

# Usage

This script can be used as a continuous process e.g a background job that keeps running in background and notifies about the slot information via sound notifications.

```
pip install -r requirements.txt
python3 slotFinder.py slotInfo.json
```

Below are the required keys to be set in `slotInfo.json`

1. dataPoints - List, A list of dictionaries define data points to query available slots
2. communicationType - String, By default this field is set as 'system'.
As soon as a slot gets available, the script shall start beeping and notify/dumps relevant information inside `slots-finder.txt` under the executing
directory. It supports Mac/Windows platform to provide slots information.
3. searchCriteria - Dictionary, It contains all the values to find a suitable slot for you. This could allow you to set search space as per your need.
Below are the key values you could define part of your search criteria,

	- minAgeLimit: String, Either could be set as a single age value e.g "18"/"45" or multiple age values e.g "18, 45"
	- vaccineName: String, Either could be set as a single vaccine name e.g "COVISHIELD"/"COVAXIN" or multiple names e.g "COVISHIELD, COVAXIN"
	- feeType: String, Either could be as e.g "Free"/"Paid" or "Free, Paid"
	- dose1: Boolean, Could be true or false
	- dose2: Boolean, Could be true or false


Feel free to use/modify the script and raise issues if it is not working for you as expected.
