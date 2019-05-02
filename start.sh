#!/bin/bash
service cron start &&
#touch log.txt &&
tail -n 100 -f log.txt
