import requests

HEADERS = {
    "Accept-Language": "hi_IN",
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

URL = "https://cdn-api.co-vin.in/api/v2/admin/location/"


def getStates():
    url = URL + "states"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print('state_id \t \tstate_name')
        print('========================================')
        for state in response.json().get('states'):
            msg = '{0}\t\t\t{1}'
            print(msg.format(state.get('state_id'), state.get('state_name')))


def getDistricts(stateId):
    url = URL + "districts/{0}".format(stateId)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print('district_id \t \tdistrict_name')
        print('========================================')
        for district in response.json().get('districts'):
            msg = '{0}\t\t\t{1}'
            print(msg.format(
                district.get('district_id'), district.get('district_name')))


if __name__ == "__main__":
    getStates()
    msg = 'Please choose state_id from the above list to get districts: '
    stateId = input(msg)
    getDistricts(stateId)
