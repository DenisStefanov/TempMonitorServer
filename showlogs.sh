while true; do clear; tail -n 22 /var/log/tempmon.log; tail -n 10 /var/log/tempmon.err; sleep 5; done
#for l in $(grep -n 'Run scenario' /var/log/tempmon.log | tail -2)
#do
#    echo $l
#done
