import os
import json
import time
import beepy
import logging
import requests
import platform
import argparse
import multiprocessing
from datetime import datetime, timedelta
from multiprocessing import Process, Lock

logging.basicConfig(level=logging.INFO,
        format="%(name)s - %(asctime)s - %(levelname)s - %(message)s")

LOCK = Lock()

def notifySlot(communicationType):
    if communicationType == 'system':
        message, title = 'Co-Win Slot Found', 'Success'
        if platform.system().lower() == 'darwin':
            command = f'''osascript -e 'display notification "{message}" with title "{title}"' '''
        beepy.beep(sound="ping")
        os.system(command)


def dumpIntoFile(center, session):
    msg = 'Found a slot near you..\n'
    msg += 'Name = {0}\n'.format(center.get('name'))
    msg += 'Address = {0}\n'.format(center.get('address'))
    msg += 'Date = {0}\n'.format(session.get('date'))
    msg += 'Available Capacity = {0}\n'.format(session.get('available_capacity'))
    msg += 'Vaccine = {0}\n'.format(session.get('vaccine'))
    msg += 'Fee Type = {0}\n'.format(center.get('fee_type'))
    msg += 'Slots = {0}\n\n'.format(session.get('slots'))

    with LOCK:
        with open('slots-finder.log', 'a') as slotFinderLogs:
            slotFinderLogs.write(msg)


def isSlotAvailable(response, searchCriteria):
    for center in response.get('centers'):
        sessions = center.get('sessions')
        for session in sessions:
            if session.get('available_capacity') > 0:
                ageLimits = searchCriteria.get('minAgeLimit').split(',')
                if str(session.get('min_age_limit')) in ageLimits:
                    vaccines = searchCriteria.get('vaccineName').split(',')
                    if session.get('vaccine') in vaccines:
                        feeTypes = searchCriteria.get('feeType').split(',')
                        if center.get('fee_type') in feeTypes:
                            msg = "{0}, {1}, {2} {3} {4} {5}"
                            msg = msg.format(session.get('available_capacity'),
                                             center.get('pincode'),
                                             center.get('name'),
                                             session.get('date'),
                                             session.get('vaccine'),
                                             center.get("fee_type"))
                            dumpIntoFile(center, session)
                            currentProcessName = multiprocessing.current_process().name
                            logging.info("{0} ==> Found with {1}".format(currentProcessName, msg))
                            return True
    return False


def getSlotInformation(dataPoint, searchBy, searchCriteria, communicationType):
    host = "https://cdn-api.co-vin.in"
    endpoint = "api/v2/appointment/sessions/public/calendarByDistrict"
    if searchBy == "pincode":
        endpoint = "api/v2/appointment/sessions/public/calendarByPin"
    url = "{0}/{1}".format(host, endpoint)

    if not dataPoint.get("date", None):
        currentHour = datetime.now().hour
        today = datetime.now()
        # after 5 PM we want to search for tomorrow
        lookupDate = today if currentHour <= 16 else today + timedelta(days=1)
        dataPoint["date"] = datetime.strftime(lookupDate, "%d-%m-%Y")

    logging.info("Sending request to '{0}' for '{1}'".format(url, dataPoint))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    response = requests.get(url, params=dataPoint, headers=headers)
    msg = "Process Name: {0} ==> Resposne Code {1}"
    logging.info(msg.format(multiprocessing.current_process().name, response.status_code))

    if response.status_code != 200:
        logging.info(response.text)
        return

    if isSlotAvailable(response.json(), searchCriteria):
        notifySlot(communicationType)


def main(inputData):
    numsOfSentRequestsPerMin = timeCounter = minutes = 0
    dataPoints = inputData.get("dataPoints", None)
    if not dataPoints:
        logging.info("No data points to poll")
        return

    numOfDataPoints = len(dataPoints)
    numsOfRequestsPerMin = 20 # Arogya setu app allows 100 requests per 5 mins
    timeToSleep = numOfDataPoints * (60 // numsOfRequestsPerMin)
    searchBy = inputData.get("searchBy", "district")
    searchCriteria = inputData.get("searchCriteria")
    communicationType =  inputData.get("communicationType", 'system')

    while True:
        if timeCounter % 60 == 0:
            msg = "Number of sent requests {0} in {1} min(s)"
            logging.info(msg.format(numsOfSentRequestsPerMin, minutes))
            minutes += 1

        searchProgresses = list()
        for dataPoint in dataPoints:
            numsOfSentRequestsPerMin += 1
            process = Process(target=getSlotInformation, args=(
                dataPoint, searchBy, searchCriteria, communicationType))
            process.start()
            searchProgresses.append(process)

        for process in searchProgresses:
            process.join()
        logging.info("Sleeping for {0} sec(s)...".format(timeToSleep))
        time.sleep(timeToSleep)
        timeCounter += timeToSleep


def parseCmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', action='store', dest='input', help='Input JSON file')

    return parser.parse_args()


if __name__ == "__main__":
    args = parseCmd()
    if not os.path.exists(args.input):
        raise FileNotFoundError("Missing Input JSON file")

    logging.info("Starting Slot-Finder with {0}".format(args))
    inputData = dict()
    with open(args.input) as inputFile:
        inputData = json.load(inputFile)

    main(inputData)

