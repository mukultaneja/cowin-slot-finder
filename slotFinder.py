'''
description
    - A continuous & multiprocessing python script to find
      an available slot for covid vaccine. As soon as a slot
      gets available based on the given search criteria this
      script starts beeping and notifying/dumping relevant
      information inside `slots-finder.log` in the executing
      directory.
usage
    - python3 slotFinder.py slotInfo.json
author
    - Mukul Taneja
'''

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
        beepy.beep(sound="ping")
        if platform.system().lower() == 'darwin':
            command = f'''osascript -e 'display notification "{message}" with title "{title}"' '''
            os.system(command)

        if platform.system().lower() == 'windows':
            from plyer import notification
            notification.notify(title=title, message=message, timeout=1)


def dumpIntoFile(center, session):
    msg = '====== Found a slot near you.. ====== \n'
    msg += 'Name = {0}\n'.format(center.get('name'))
    msg += 'Address = {0}\n'.format(center.get('address'))
    msg += 'Date = {0}\n'.format(session.get('date'))
    msg += 'Available Capacity = {0}\n'.format(session.get('available_capacity'))
    msg += 'Vaccine = {0}\n'.format(session.get('vaccine'))
    msg += 'Fee Type = {0}\n'.format(center.get('fee_type'))
    msg += 'Slots = {0}\n'.format(session.get('slots'))
    msg += 'Pincode = {0}\n'.format(center.get('pincode'))
    msg += 'District Name = {0}\n'.format(center.get('district_name'))
    msg += '==================================== \n\n'

    with LOCK:
        with open('slots-finder.txt', 'a') as slotFinderLogs:
            slotFinderLogs.write(msg)


def isSlotAvailable(response, searchCriteria):
    for center in response.get('centers'):
        sessions = center.get('sessions')
        for session in sessions:
            if session.get('available_capacity') > 0:
                ageLimits = searchCriteria.get('minAgeLimit').split(',')
                ageLimits = [ageLimit.strip() for ageLimit in ageLimits]
                if str(session.get('min_age_limit')) in ageLimits:
                    vaccines = searchCriteria.get('vaccineName').split(',')
                    vaccines = [vaccine.strip() for vaccine in vaccines]
                    if session.get('vaccine') in vaccines:
                        feeTypes = searchCriteria.get('feeType').split(',')
                        feeTypes = [feeType.strip() for feeType in feeTypes]
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


def getSlotInformation(dataPoint, searchCriteria, communicationType):
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public"
    endpoint = "calendarByPin" if dataPoint.get("pincode") else "calendarByDistrict"
    url = "{0}/{1}".format(url, endpoint)

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
    searchCriteria = inputData.get("searchCriteria")
    communicationType =  inputData.get("communicationType", 'system')

    while True:
        if timeCounter % 60 == 0:
            msg = "======= Number of sent requests {0} in {1} min(s) ======="
            logging.info(msg.format(numsOfSentRequestsPerMin, minutes))
            minutes += 1

        searchProcesses = list()
        for dataPoint in dataPoints:
            numsOfSentRequestsPerMin += 1
            process = Process(target=getSlotInformation,
                              args=(dataPoint, searchCriteria, communicationType))
            process.start()
            searchProcesses.append(process)

        for process in searchProcesses:
            process.join()

        logging.info("Sleeping for {0} sec(s)...".format(timeToSleep))
        time.sleep(timeToSleep)
        timeCounter += timeToSleep


def parseCmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Input JSON file')

    return parser.parse_args()


if __name__ == "__main__":
    args = parseCmd()
    if not os.path.exists(args.input):
        raise FileNotFoundError("No file found named {0}".format(args.input))

    logging.info("Starting Slot-Finder with {0}".format(args))
    inputData = dict()
    with open(args.input) as inputFile:
        inputData = json.load(inputFile)

    main(inputData)

