run=$(curl -s https://wtos.nl/bc/run.php?q)
[ $run == true ] && cd /src && date >> log.txt && /usr/local/bin/python wtosbc/main.py >> log.txt && curl -s -o /dev/null https://wtos.nl/bc/run.php?done
