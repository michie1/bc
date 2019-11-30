#!/bin/bash
service cron start &&
tail -n 100 -f log.txt
