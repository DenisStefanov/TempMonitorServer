curl -b session.txt -c session.txt http://192.168.8.1/html/index.html > /dev/null 2>&1
TOKEN=$(curl -s -b session.txt -c session.txt http://192.168.8.1/html/smsinbox.html | grep csrf_token | tail -1 | cut -d '"' -f 4)

NUMBER=$1
MESSAGE=$2

LENGTH=${#MESSAGE}

TIME=$(date +"%Y-%m-%d %T")

SMS="<?xml version='1.0' encoding='UTF-8'?><request><Index>-1</Index><Phones><Phone>$NUMBER</Phone></Phones><Content>$MESSAGE</Content><Length>$LENGTH</Length><Reserved>1</Reserved><Date>$TIME</Date></request>"

curl -v -b session.txt -c session.txt -H "X-Requested-With: XMLHttpRequest" --data "$SMS" http://192.168.8.1/api/sms/send-sms --header "__RequestVerificationToken: $TOKEN" --header "Content-Type:text/xml" > /dev/null 2>&1
