#!/usr/bin/env python

import datetime
import time

import schedule


def job():
    print(datetime.datetime.now())


schedule.every().minutes.do(job)

schedule.run_all()

while True:
    schedule.run_pending()
    time.sleep(1)
