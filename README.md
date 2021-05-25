# cowin-slot-finder

A tool to find available vaccination slots for covid vaccine using Co-WIN [public](https://apisetu.gov.in/public/api/cowin) APIs. `slotFinder.py` is a python script that helps to search available slots using pincode or district. It is a continous, multi-processing based script that can take multiple pincodes or districts to find slots at a time and smart enough to manage time difference between multiple requests to the server. The intention is to never cross `100 requests in 5 mins` boundary imposed by the Co-Win public APIs

Once you start the script, it keeps polling the slots and starts notifying as soon as once available for you.

# Requirements
1. Python 3

# Usage
```

pip install -r requirements.txt
python3 slotFinder.py --input slotInfo.json

```

Below are the required keys to be set in `slotInfo.json`

```

1. searchBy - String, Either could be set as 'pincode' or 'district'

2. dataPoints - List, A list of dictionaries define data points to query available slots

3. communicationType - String, by default this field is set as 'system' that means as soon as a
slot gets available, the script shall start beeping to notify you on the sane.
Currently it only supports Mac platform but soon it will support Windows platform too.

4. searchCriteria - Dictionary, It contains all the values to find a suitable slot for you.
This could allow you to set search space as per your need.
Below are the key values you could define part of your search criteria,

- minAgeLimit: String, Either could be set as a single age value e.g "18"/"45" or multiple age values e.g "18,45"
- vaccineName: String, Either could be set as a single vaccine name e.g "COVISHIELD"/"COVAXIN" or multiple names e.g "COVISHIELD,COVAXIN"
- feeType: String, Either could be as e.g "Free"/"Paid" or "Free,Paid"

```


Feel free to use/modify the script and raise issues if it is not working for you as expected.
