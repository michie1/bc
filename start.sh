#!/bin/bash
service cron start &&
touch log.txt &&
tail -f log.txt
