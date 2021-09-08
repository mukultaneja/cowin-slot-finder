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
    - mukultaneja91@gmail.com
'''

import os
import sys
import json
import time
import beepy
import logging
import requests
import platform
import argparse
import multiprocessing
from prettytable import PrettyTable
from datetime import datetime, timedelta
from multiprocessing import Process, Lock
from logging.handlers import TimedRotatingFileHandler


formatter = logging.Formatter(
    "%(name)s - %(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

file_handler = TimedRotatingFileHandler("slots-finder.log", when='midnight')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger = logging.getLogger('root')
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

LOCK = Lock()


def notifySlot(communicationType, silentNotifier):
    if communicationType == 'system':
        message, title = 'Co-Win Slot Found', 'Success'
        if not silentNotifier:
            beepy.beep(sound="ping")

        if platform.system().lower() == 'darwin':
            command = f'''osascript -e 'display notification "{message}" with title "{title}"' '''
            os.system(command)

        if platform.system().lower() == 'windows':
            from plyer import notification
            notification.notify(title=title, message=message, timeout=1)


def dumpIntoFile(availableSlots):
    with LOCK:
        slots = list()
        for session in availableSlots:
            slots.append({
                'date': session.get('date'),
                'capacity': session.get('available_capacity'),
                'fee': "Free" if session.get('fee') == "0" else "Paid",
                'dose1': session.get("available_capacity_dose1"),
                'dose2': session.get("available_capacity_dose2"),
                'vaccine': session.get('vaccine'),
                'bookingTime': datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M:%S'),
                'pincode': session.get('pincode')
            })
        data = list()
        if os.path.exists('slots-finder.json'):
            f = open('slots-finder.json')
            data = json.load(f)
            f.close()
        data.extend(slot)
        with open('slots-finder.json', 'w') as f:
            json.dump(data, f, indent=4)


def getAvailableSlot(response, searchCriteria):
    ageLimits = [ageLimit.strip()
                 for ageLimit in searchCriteria.get('minAgeLimit').split(',')]
    vaccines = [vaccine.strip()
                for vaccine in searchCriteria.get('vaccineName').split(',')]
    feeTypes = [feeType.strip()
                for feeType in searchCriteria.get('feeType').split(',')]

    availableSlots = list()
    slotTable = PrettyTable()
    slotTable.field_names = ['Name', 'PinCode', 'Vaccine Name', 'Fee',
                             'Date', 'Dose1', 'Dose2']
    for session in response.get('sessions'):
        if session.get('available_capacity') > 0:
            if str(session.get('min_age_limit')) in ageLimits:
                if session.get('vaccine') in vaccines:
                    feeType = "Free" if session.get('fee') == "0" else "Paid"
                    if feeType in feeTypes:
                        if searchCriteria.get("dose1") and \
                                session.get("available_capacity_dose1") > 0:
                            availableSlots.append(session)
                        elif searchCriteria.get("dose2") and \
                                session.get("available_capacity_dose2") > 0:
                            availableSlots.append(session)

    for availableSlot in availableSlots:
        slotTable.add_row([availableSlot.get('name'),
                           availableSlot.get('pincode'),
                           availableSlot.get('vaccine'),
                           availableSlot.get("fee"),
                           availableSlot.get('date'),
                           availableSlot.get("available_capacity_dose1"),
                           availableSlot.get("available_capacity_dose2")])

    if availableSlots:
        for line in slotTable.get_string().splitlines():
            print('\t' + line + '\n')

    return availableSlots


def findSlot(dataPoint, extraArgs):
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public"
    endpoint = "findByPin" if dataPoint.get("pincode") else "findByDistrict"
    url = "{0}/{1}".format(url, endpoint)
    if not dataPoint.get("date", None):
        currentHour = datetime.now().hour
        today = datetime.now()
        # after 5 PM we want to search for tomorrow
        lookupDate = today if currentHour <= 16 else today + timedelta(days=1)
        dataPoint["date"] = datetime.strftime(lookupDate, "%d-%m-%Y")

    logger.info("Sending request to '{0}' for '{1}'".format(url, dataPoint))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    }

    response = requests.get(url, params=dataPoint, headers=headers)
    msg = "Process Name: {0} ==> Resposne Code {1}"
    msg = msg.format(multiprocessing.current_process().name, response.status_code)
    logger.info(msg)
    logger.debug(response.json())
    if response.status_code != 200:
        logger.info(response.text)
        return

    availableSlots = getAvailableSlot(
        response.json(), extraArgs.get('searchCriteria'))
    if availableSlots:
        if extraArgs.get('analyzerFlag'):
            dumpIntoFile(availableSlots)
        notifySlot(extraArgs.get('communicationType'),
                   extraArgs.get('silentNotifier'))


def main(args):
    inputData = dict()
    with open(args.input) as inputFile:
        inputData = json.load(inputFile)
    dataPoints = inputData.get("dataPoints", None)
    if not dataPoints:
        logger.info("No data points to poll")
        return
    numOfDataPoints = len(dataPoints)
    numsOfRequestsPerMin = 20  # Arogya setu app allows 100 requests per 5 mins
    timeToSleep = numOfDataPoints * (60 // numsOfRequestsPerMin)
    extraArgs = {
        'searchCriteria': inputData.get("searchCriteria"),
        'communicationType': inputData.get("communicationType", 'system'),
        'silentNotifier': args.silent,
        'analyzerFlag': args.analyze

    }
    numsOfSentRequestsPerMin = timeCounter = minutes = 0
    while True:
        searchProcesses = list()
        if timeCounter % 60 == 0:
            msg = "======= Number of sent requests {0} in {1} min(s) ======="
            logger.info(msg.format(numsOfSentRequestsPerMin, minutes))
            minutes += 1

        for dataPoint in dataPoints:
            numsOfSentRequestsPerMin += 1
            process = Process(target=findSlot, args=(dataPoint, extraArgs))
            process.start()
            searchProcesses.append(process)

        for process in searchProcesses:
            process.join()

        logger.info("Sleeping for {0} sec(s)...".format(timeToSleep))
        time.sleep(timeToSleep)
        timeCounter += timeToSleep


def parseCmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Input JSON file')
    parser.add_argument('--silent', help='a flag for a slient notifier',
                        action='store_true')
    parser.add_argument('--analyze', help='a flag to start slot analysis',
                        action='store_true')

    return parser.parse_args()


if __name__ == "__main__":
    args = parseCmd()
    if not os.path.exists(args.input):
        raise FileNotFoundError("No file found named {0}".format(args.input))

    logger.info("Starting Slot-Finder with {0}".format(args))
    main(args)
