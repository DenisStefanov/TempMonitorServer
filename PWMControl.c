#include <stdio.h>
#include <stdlib.h>     /* atof */
#include <sys/time.h>
#include <errno.h>
#include <string.h>
#include <wiringPi.h>

// Which GPIO pin we're using
#define ZCDPin 5
#define PWMPin 4
#define DIM_FILE "/home/pi/TempMonitorServer/dimval.txt"
volatile double dimming;

//struct timeval tm1, tm2;

void ZCDHandle(void) {

  //gettimeofday(&tm1, NULL);
  //printf("%d.%d, %d.%d\n", tm1.tv_sec, tm1.tv_usec/1000, tm2.tv_sec, tm2.tv_usec/1000);
  //printf("%d, %d\n", tm1.tv_sec+tm1.tv_usec/1000, tm2.tv_sec+tm2.tv_usec/1000);
  //int timediff = ((tm1.tv_sec * 1000 * 1000 + tm1.tv_usec) - (tm2.tv_sec * 1000 * 1000 + tm2.tv_usec)) / 1000;
  //gettimeofday(&tm2, NULL);

  /*  if (timediff !=10)
    {
      printf("ZCDHandle %d SKIPPING\n", timediff);
      return;
    }
  */
  // Firing angle calculation :: 50Hz-> 10ms (1/2 Cycle)
  // (10000us - 10us) / 128 = 75 (Approx)
  int dimtime = (int)(75*dimming);
  delayMicroseconds(dimtime);    // Off cycle
  digitalWrite(PWMPin, HIGH);   // triac firing
  delayMicroseconds(20);         // triac On propogation delay
  digitalWrite(PWMPin, LOW);    // triac Off
  
  //printf("ZCDHandle time=%d diming=%d\n", dimtime, dimming);
  
}

double readDim()
{
  char numstr[6];
  FILE *fp;
  double num;


  fp = fopen(DIM_FILE, "r");

  if (fp == NULL)
    {
      perror("Error while opening the file.\n");
      return 0;
    }


  fgets(numstr, sizeof(numstr), fp);
  num = atof(numstr);
  
  fclose(fp);
  return num;
}

int main(void) {

  if (wiringPiSetup () < 0) {
    fprintf (stderr, "Unable to setup wiringPi: %s\n", strerror (errno));
    return 1;
  }

  pinMode(PWMPin, OUTPUT);
  pinMode(ZCDPin, INPUT);
  pullUpDnControl (ZCDPin, PUD_DOWN);
  
  if ( wiringPiISR (ZCDPin, INT_EDGE_FALLING, &ZCDHandle) < 0 ) {
    fprintf (stderr, "Unable to setup ISR: %s\n", strerror (errno));
    return 1;
  }

  for (;;) {
    dimming = 120 - readDim();
  // printf("dimming=%f readDim=%f\n", dimming, readDim());
  // for(dimming=115; dimming>=0; dimming--)
    delay(1000);
  }
  
}
