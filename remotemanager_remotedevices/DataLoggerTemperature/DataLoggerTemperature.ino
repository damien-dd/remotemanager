/*
  SD card datalogger
 
 This example shows how to log data from three analog sensors 
 to an SD card using the SD library.
 	
 The circuit:
 * analog sensors on analog ins 0, 1, and 2
 * SD card attached to SPI bus as follows:
 ** MOSI - pin 11
 ** MISO - pin 12
 ** CLK - pin 13
 ** CS - pin 4
 
 created  24 Nov 2010
 modified 9 Apr 2012
 by Tom Igoe
 
 This example code is in the public domain.
 	 
 */

#include <avr/pgmspace.h>
#include <avr/wdt.h>
#include <string.h>
#include <SD.h>
#include <Wire.h>
#include <math.h>
#include <TimerOne.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "DS1307.h"

#define MAX_CMD_LENGTH 48

#define ERR_EXISTING_DATA 1
#define ERR_SD_CARD 2
#define ERR_RTC 4

// On the Ethernet Shield, CS is pin 4. Note that even if it's not
// used as the CS pin, the hardware CS pin (10 on most Arduino boards,
// 53 on the Mega) must be left as an output or the SD library
// functions will not work.
const int chipSelect = 4;

const int tempPin = 0;

char cmd[MAX_CMD_LENGTH+5];
int cmdLength = 0;   // for incoming serial data

DS1307 clock;//define a object of DS1307 class


#define TEMPERATURE_PRECISION 12 //12bits resolution
#define WH_PER_UNIT 1 //Wh per 0.0625°C


#define T_S1_CIRCULATOR_ENABLE 950 //enable circulator if T(S1) >= 95.0°C
#define T_S1_CIRCULATOR_DISABLE 900 //disable circulator if T(S1) < 90.0°C
//#define T_DIFF_S1_S2_CIRCULATOR_ENABLE 60 //enable circulator if T(S1)-T(S2) > 6.0°C
//#define T_DIFF_S1_S2_CIRCULATOR_DISABLE 50 //disable circulator if T(S1)-T(S2) < 5.0°C

#define CIRCULATOR_DETECTION_PIN 9
#define CIRCULATOR_RELAY_PIN 8

// We use 1bus per sensor
#define ONE_WIRE_BUS1 2
#define ONE_WIRE_BUS2 3
#define ONE_WIRE_BUS3 5

// Setup oneWire instances to communicate with OneWire devices
OneWire oneWire1(ONE_WIRE_BUS1);
OneWire oneWire2(ONE_WIRE_BUS2);
OneWire oneWire3(ONE_WIRE_BUS3);

// Pass oneWire references to Dallas Temperature. 
DallasTemperature sensorIn(&oneWire1);
DallasTemperature sensorOut(&oneWire2);
DallasTemperature sensor(&oneWire3);

volatile unsigned char err_flags = 0;
volatile unsigned char ovf_flags = 0;
volatile unsigned char err_rtc = 0;


volatile byte lock_mutex = 0;
volatile byte temp_clear = 0;
volatile int tempIn = -1;
volatile int tempOut = -1;
volatile int temp = -1;
volatile int tempS1 = -1;
volatile int tempS2 = -1;
volatile int tempS3 = -1;


volatile unsigned int cnt = 0;
volatile byte cnt_clear = 0;
volatile unsigned long cnt_total = 0;


volatile unsigned int nbSavePoints_total=0;
volatile unsigned int nbSavePoints_err=0;
volatile unsigned int nbSavePoints_ok=0;
volatile unsigned int sdCardErrCounter=0;
volatile unsigned int rtcErrCounter=0;
volatile unsigned int sensor1ErrCounter=0;
volatile unsigned int sensor2ErrCounter=0;
volatile unsigned int sensor3ErrCounter=0;

volatile int8_t timeout;

volatile int16_t temperatureIn=-1;
volatile int16_t temperatureOut=-1;
volatile int16_t temperature=-1;
volatile int16_t temperatureS1=-1;
volatile int16_t temperatureS2=-1;
volatile int16_t temperatureS3=-1;


uint8_t isDigit(uint8_t car)
{
  if(car >= '0' && car <= '9')
    return 1;
  else
    return 0;
}

uint8_t int2hexDigit(uint8_t v)
{
  if(v >= 0 && v <= 9)
    return '0'+v;
  else if(v >= 10 && v <=15)
    return 'A'-10+v;
  else return '?';
}

/// --------------------------
/// Custom ISR Timer Routine
/// --------------------------
void timerIsr()
{
  static uint32_t temp_sum=0, tempIn_sum=0, tempOut_sum=0, tempS1_sum=0, tempS2_sum=0, tempS3_sum=0;
  static uint8_t temp_nb=0, tempIn_nb=0, tempOut_nb=0, tempS1_nb=0, tempS2_nb=0, tempS3_nb=0;
  
  timeout--;
  
  if (sensorIn.getResolutionByIndex(0) != TEMPERATURE_PRECISION)
  {
    initTemperatureSensor(&sensorIn);
    temperatureIn=-1;
  }
  else
    temperatureIn=sensorIn.getTempRawByIndex(0)+64*16;
  
  if (sensorOut.getResolutionByIndex(0) != TEMPERATURE_PRECISION)
  {
    initTemperatureSensor(&sensorOut);
    temperatureOut=-1;
  }
  else
    temperatureOut=sensorOut.getTempRawByIndex(0)+64*16;
    
  if (sensor.getResolutionByIndex(0) != TEMPERATURE_PRECISION)
  {
    initTemperatureSensor(&sensor);
    temperature=-1;
  }
  else
    temperature=sensor.getTempRawByIndex(0)+64*16;
    
  temperatureS1 = ((uint32_t)analogRead(A0)*6355)/1024 - 4233 + 640; //6303*(1800k+15k)/1800k=6355
  temperatureS2 = ((uint32_t)analogRead(A1)*6355)/1024 - 4233 + 640; //6303*(1800k+15k)/1800k=6355
  temperatureS3 = ((uint32_t)analogRead(A2)*6346)/1024 - 4233 + 640; //6303*(2200k+15k)/2200k=6346
    
  if(temperatureIn < 0)
    sensor1ErrCounter++;
  if(temperatureOut < 0)
    sensor2ErrCounter++;
  if(temperature < 0)
    sensor3ErrCounter++;
  
  if(cnt_clear)
  {
    cnt_total+=cnt;
    cnt=0;
    cnt_clear=0;
  }
    
  if(temperatureIn > 0 && temperatureOut > 0 && temperatureOut > temperatureIn && !digitalRead(CIRCULATOR_DETECTION_PIN))
  {
    cnt+=(uint32_t)(((uint32_t)(((uint32_t)((uint32_t)318 * (uint16_t)( (temperatureOut-64*16) + (temperatureIn-64*16) ) ) + (uint32_t)5689744) )/8) * (uint16_t)(temperatureOut-temperatureIn)) >> 20;
  }
  
  if(temp_clear)
  {
    tempIn_sum=0;
    tempIn_nb=0;
    
    tempOut_sum=0;
    tempOut_nb=0;
    
    temp_sum=0;
    temp_nb=0;
    
    tempS1_sum=0;
    tempS1_nb=0;
    tempS2_sum=0;
    tempS2_nb=0;
    tempS3_sum=0;
    tempS3_nb=0;
    
    temp_clear=0;
  }
  
  if(temperatureIn > 0)
  {
    tempIn_sum+=temperatureIn;
    tempIn_nb++;
    if(!lock_mutex)
        tempIn=tempIn_sum/tempIn_nb;
  }
  else if(!lock_mutex)
    tempIn=-1;
    
  if(temperatureOut > 0)
  {
    tempOut_sum+=temperatureOut;
    tempOut_nb++;
    if(!lock_mutex)
        tempOut=tempOut_sum/tempOut_nb;
  }
  else if(!lock_mutex)
    tempOut=-1;
    
  if(temperature > 0)
  {
    temp_sum+=temperature;
    temp_nb++;
    if(!lock_mutex)
        temp=temp_sum/temp_nb;
  }
  else if(!lock_mutex)
    temp=-1;
    
  if(temperatureS1 > 0 && temperatureS1 < 2500)
  {
    if(temperatureS1 >= 640 + T_S1_CIRCULATOR_ENABLE)
      digitalWrite(CIRCULATOR_RELAY_PIN, HIGH);
    else if(temperatureS1 < 640 + T_S1_CIRCULATOR_DISABLE)
      digitalWrite(CIRCULATOR_RELAY_PIN, LOW);
    tempS1_sum+=temperatureS1;
    tempS1_nb++;
    if(!lock_mutex)
        tempS1=tempS1_sum/tempS1_nb;
  }
  else
  {
    digitalWrite(CIRCULATOR_RELAY_PIN, LOW);
    if(!lock_mutex)
      tempS1=-1;
  }
    
  if(temperatureS2 > 0 && temperatureS2 < 2500)
  {
    tempS2_sum+=temperatureS2;
    tempS2_nb++;
    if(!lock_mutex)
        tempS2=tempS2_sum/tempS2_nb;
  }
  else if(!lock_mutex)
    tempS2=-1;
    
  if(temperatureS3 > 0 && temperatureS3 < 2500)
  {
    tempS3_sum+=temperatureS3;
    tempS3_nb++;
    if(!lock_mutex)
        tempS3=tempS3_sum/tempS3_nb;
  }
  else if(!lock_mutex)
    tempS3=-1;

  //start conversions on all sensors
  sensorIn.requestTemperatures();
  sensorOut.requestTemperatures();
  sensor.requestTemperatures();
  
  wdt_reset();
}

void initTemperatureSensor(DallasTemperature* TempSensor)
{
  // we put a different resolution in RAM and EEPROM so we can
  // know when if the sensor has been disconnected/reconnected
  // and need to be reinitialized
  TempSensor->begin();
  TempSensor->setResolution(9);
  TempSensor->setEepromEnable(false);
  TempSensor->setResolution(TEMPERATURE_PRECISION);
  TempSensor->setWaitForConversion(false);
  TempSensor->requestTemperatures();
}

void setup()
{
  wdt_disable();
  wdt_enable(WDTO_8S);
  
  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  
  analogReference(EXTERNAL);
  
  pinMode(CIRCULATOR_DETECTION_PIN, INPUT_PULLUP);
  
  pinMode(CIRCULATOR_RELAY_PIN, OUTPUT);
  digitalWrite(CIRCULATOR_RELAY_PIN, LOW);
  
  clock.begin();
  clock.startClock();
  
  // initialize temperature sensors
  initTemperatureSensor(&sensorIn);
  initTemperatureSensor(&sensorOut);
  initTemperatureSensor(&sensor);
  
  delay(1000);
  
  Timer1.initialize(1000000); // set a timer of length 100000 microseconds (or 0.1 sec - or 10Hz => the led will blink 5 times, 5 cycles of on-and-off, per second)
  Timer1.attachInterrupt( timerIsr ); // attach the service routine here

  // make sure that the default chip select pin is set to
  // output, even if you don't use it:
  pinMode(10, OUTPUT);
}

int readRTC(char *buffer)
{
  clock.getTime();

  if((clock.year >= 0 && clock.year < 100) &&
     (clock.month > 0 && clock.month <= 12) &&
     (clock.dayOfMonth > 0 && clock.dayOfMonth <= 31))
  {
    *(buffer++)='0' + clock.year/10;
    *(buffer++)='0' + clock.year%10;
    *(buffer++)='-';
    *(buffer++)='0' + clock.month/10;
    *(buffer++)='0' + clock.month%10;
    *(buffer++)='-';
    *(buffer++)='0' + clock.dayOfMonth/10;
    *(buffer++)='0' + clock.dayOfMonth%10;
    *(buffer++)=0;
    return 0;
  }
  else
    return 1;
}

void handle_serial()
{
  if (Serial.available() > 0) {
    cmdLength = Serial.readBytesUntil('\r', cmd, MAX_CMD_LENGTH);
    
    if(cmdLength == 0)
      Serial.println(F("E01"));
    else if(cmdLength == MAX_CMD_LENGTH)
      Serial.println(F("E02"));
    else if(cmdLength == 4 && !strncmp_P(cmd, PSTR("PING"), cmdLength))
    {
      Serial.println("p");
    }
    else if(cmdLength == 8 && !strncmp_P(cmd, PSTR("READ_ALL"), cmdLength))
    {
      Serial.print(F("Tin: "));
      if(temperatureIn > 0)
        Serial.print(float(temperatureIn-64*16)/16, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
      
      Serial.print(F("Tout: "));
      if(temperatureOut > 0)
        Serial.print(float(temperatureOut-64*16)/16, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
        
      Serial.print(F("T: "));
      if(temperature > 0)
        Serial.print(float(temperature-64*16)/16, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
        
      Serial.print(F("S1: "));
      if(temperatureS1 > 0 && temperatureS1 < 2500)
        Serial.print(float(temperatureS1-640)/10, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
        
      Serial.print(F("S2: "));
      if(temperatureS2 > 0 && temperatureS2 < 2500)
        Serial.print(float(temperatureS2-640)/10, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
        
      Serial.print(F("S3: "));
      if(temperatureS3 > 0 && temperatureS3 < 2500)
        Serial.print(float(temperatureS3-640)/10, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
      
      Serial.print(F("Circulator: "));
      if(digitalRead(CIRCULATOR_DETECTION_PIN))
        Serial.println(F("OFF"));
      else
        Serial.println(F("ON"));
      Serial.print(F("\r\n"));
    }
    else if(cmdLength == 6 && !strncmp_P(cmd, PSTR("STATUS"), cmdLength))
    {
      Serial.print("e");
      Serial.println(err_flags|ovf_flags, HEX);
    }
    else if(cmdLength == 8 && !strncmp_P(cmd, PSTR("GET_TIME"), cmdLength))
    {
      clock.getTime();
      if((clock.year >= 0 && clock.year < 100) &&
         (clock.month > 0 && clock.month <= 12) &&
         (clock.dayOfMonth > 0 && clock.dayOfMonth <= 31) &&
         (clock.hour >= 0 && clock.hour < 24) &&
         (clock.minute >= 0 && clock.minute < 60) &&
         (clock.second >= 0 && clock.second < 60))
      {
        Serial.print(clock.dayOfMonth);
        Serial.print('/');
        Serial.print(clock.month);
        Serial.print('/');
        Serial.print(clock.year);
        Serial.print(' ');
        Serial.print(clock.hour);
        Serial.print(':');
        Serial.print(clock.minute);
        Serial.print(':');
        Serial.println(clock.second);
      }
      else
        Serial.println(F("E20"));
    }
    else if(cmdLength == 9+8+1+8 && !strncmp_P(cmd, PSTR("SET_TIME:"), 9) &&
            cmd[11] == '/' && cmd[14] == '/' && cmd[17] == ' ' &&
            cmd[20] == ':' && cmd[23] == ':')
    {
      unsigned int year, month, day, hours, minutes, seconds;
      
      cmd[9+8+1+8] = 0;
      day=strtoul(cmd+9, NULL, DEC);
      month=strtoul(cmd+12, NULL, DEC);
      year=strtoul(cmd+15, NULL, DEC);
      hours=strtoul(cmd+18, NULL, DEC);
      minutes=strtoul(cmd+21, NULL, DEC);
      seconds=strtoul(cmd+24, NULL, DEC);

      if((day > 0 && day <= 31) &&
         (month > 0 && month <= 12) &&
         (year > 0 && year <= 99) &&
         (hours >= 0 && hours < 24) &&
         (minutes >= 0 && minutes < 60) &&
         (seconds >= 0 && seconds < 60))
      {
        clock.fillByYMD(2000+year, month, day);
        clock.fillByHMS(hours, minutes, seconds);
        clock.setTime();
      }
      else
        Serial.println(F("E04"));
    }
    else if(cmdLength == 13 && !strncmp_P(cmd, PSTR("SHOW_COUNTERS"), cmdLength))
    {
      Serial.print(F("CNT:"));
      Serial.println(cnt);
      Serial.print(F("CNT total:"));
      Serial.println(cnt_total);
      Serial.print(F("Temperature:"));
      Serial.println(temp);
      Serial.print(F("\r\n"));
    }
    else if(cmdLength == 12 && !strncmp_P(cmd, PSTR("READ_ERR_CNT"), cmdLength))
    {
      Serial.print(F("Save point:"));
      Serial.println(nbSavePoints_err);
      Serial.print(F("SD:"));
      Serial.println(sdCardErrCounter);
      Serial.print(F("RTC:"));
      Serial.println(rtcErrCounter);
      Serial.print(F("Sensor1:"));
      Serial.println(sensor1ErrCounter);
      Serial.print(F("Sensor2:"));
      Serial.println(sensor2ErrCounter);
      Serial.print(F("Sensor3:"));
      Serial.println(sensor3ErrCounter);
      Serial.print(F("Success:"));
      Serial.println(nbSavePoints_ok);
      Serial.print(F("\r\n"));
    }
    else if(cmdLength == 20+8+4+4 && !strncmp_P(cmd, PSTR("GET_DATA_FILES_LIST:"), 20))
    {
      if(SD.begin(chipSelect))
      {
        char buffer[16]="xxLIST.log";

        buffer[0] = cmd[20+0];
        buffer[1] = cmd[20+1];

        File dataFile = SD.open(buffer, FILE_READ);
        if(dataFile)
        {
          uint16_t start_at, nb_files;
          int dataavailable;
          
          cmd[20+8+4] = 0;
          start_at = strtoul(cmd+20+8+1, NULL, DEC);
          
          cmd[20+8+4+4] = 0;
          nb_files = strtoul(cmd+20+8+1+4, NULL, DEC);

          dataavailable=dataFile.available();
          for(uint16_t f=0; dataavailable >= 10 && nb_files > 0; f++)
          {
            for(uint8_t i=0; i<10; i++)
              buffer[i]=dataFile.read();

            if(f == 0)
            {
              if(strncmp(cmd+20, buffer, 8))
                 start_at=0;
                 
              for(uint8_t i=0; i<8; i++)
                Serial.write(buffer[i]);
                
              Serial.write(',');
              if(start_at < 100)
                Serial.write('0');
              if(start_at < 10)
                Serial.write('0');
              Serial.print(start_at);
              
              Serial.write(',');
              if(dataavailable < (start_at+nb_files)*10)
                nb_files=dataavailable/10-start_at;
              if(nb_files < 100)
                Serial.write('0');
              if(nb_files < 10)
                Serial.write('0');
              Serial.println(nb_files);
              
            }
            
            if(f >= start_at)
            {
              for(uint8_t i=0; i<10; i++)
                Serial.write(buffer[i]);
              nb_files--;
            }
            dataavailable-=10;
          }
          dataFile.close();
        }
        else
          Serial.println(F("E11"));
      }
      else
        Serial.println(F("E10"));
    }
    else if((!strncmp_P(cmd, PSTR("GET_DATA_RAW:"), 13) && cmdLength==13+8+3 && cmd[13+8]==',') || (!strncmp_P(cmd, PSTR("GET_DATA_SUM:"), 13) && cmdLength==13+8) || (!strncmp_P(cmd, PSTR("GET_DATA_AVG:"), 13) && cmdLength==13+8))
    {
      if(SD.begin(chipSelect))
      {
        char str[5];
        
        str[1] = cmd[13+8+1];
        str[2] = cmd[13+8+2];
        str[3] = 0;
        
        cmd[13+8]='.';
        cmd[13+8+1]='l';
        cmd[13+8+2]='o';
        cmd[13+8+3]='g';
        cmd[13+8+4]=0;
        File dataFile = SD.open(cmd+13, FILE_READ);
            
        if(dataFile)
        {
          unsigned int nbchars=0;
          unsigned int dataavailable=0;
          unsigned long sum=0;
          byte cnt=0;
          
          
          do
          {
            nbchars++;
            if(cmd[9]=='R')
            {
              uint16_t begin_at = 0, end_at=0;
              
              if(str[1] == 'x' && str[2] == 'x')
              {
                begin_at = 0;
                end_at = (2+3+4*60)*24;
              }
              else if(isDigit(str[1]) && isDigit(str[2]))
              {
                begin_at = strtoul(str+1, NULL, DEC)*(2+3+4*60);
                end_at = begin_at + 2+3+4*60;
              }
              else
                Serial.print(F("E04"));
              
              str[0] = dataFile.read();
              dataavailable=dataFile.available();
              
              if(nbchars > begin_at && nbchars <= end_at)
                Serial.write(str[0]);
              else if(nbchars >= end_at)
                dataavailable = 0;
            }
            else
            {
              str[3] = dataFile.read();
              dataavailable=dataFile.available();
              if(str[3] == 'h')
              {
                sum = 0;
                cnt = 0;
                str[4] = 0;
                
                Serial.print(str+1);
              }
              else if(str[3] == ',' || str[3] == '\r' || dataavailable == 0)
              {
                if(dataavailable == 0)
                {
                  str[0] = str[1];
                  str[1] = str[2];
                  str[2] = str[3];
                }
                str[3] = 0;
                
                if((isDigit(str[0]) || (str[0]>='A' && str[0]<='F')) &&
                   (isDigit(str[1]) || (str[1]>='A' && str[1]<='F')) &&
                   (isDigit(str[2]) || (str[2]>='A' && str[2]<='F')))
                {
                  cnt++;
                  sum += strtoul(str, NULL, HEX);
                }
                
              }
              else
              {
                str[0] = str[1];
                str[1] = str[2];
                str[2] = str[3];
              }
              
              if((str[3] == '\n' || dataavailable == 0) && nbchars > 5)
              {
                if(cnt < 10)
                  Serial.print('0');
                Serial.print(cnt);
                  
                if(cnt==60)
                  Serial.print(F("C:"));
                else
                  Serial.print(F("I:"));
                  
                if(cmd[9]=='A')
                {
                  if(cnt>0) //DATA_READ_AVG
                    sum = sum/cnt;
                }
                else
                {
                  if(sum < 0x100000)
                    Serial.print('0');
                  if(sum < 0x10000)
                    Serial.print('0');
                }
                if(sum < 0x1000)
                  Serial.print('0');
                if(sum < 0x100)
                  Serial.print('0');
                if(sum < 0x10)
                  Serial.print('0');
                Serial.print(sum, HEX);
                Serial.print(F("\r\n"));
              }
              
            }
          }while(dataavailable);
          dataFile.close();
        }
        else
          Serial.println(F("E11"));
      }
      else
        Serial.println(F("E10"));
    }
    else if(!strncmp_P(cmd, PSTR("RM_DATA_FILE:"), 13) && cmdLength==13+8)
    {
      if(SD.begin(chipSelect))
      {
        cmd[13+8]='.';
        cmd[13+8+1]='l';
        cmd[13+8+2]='o';
        cmd[13+8+3]='g';
        cmd[13+8+4]=0;
        if(SD.remove(cmd+13))
          Serial.println(F("OK!"));
        else
          Serial.println(F("E11"));
      }
    }
    else
      Serial.println(F("E03"));
  }
}

void loop()
{
  err_rtc=0;
  clock.getTime();

  if(clock.second >= 0 && clock.second < 60)
  {
    timeout=60-clock.second+1;
    while(timeout > 0)
    {
      handle_serial();
      delay(100);
      
      //Serial.print(".");
    }
    
    clock.getTime();
    //Serial.print("sec:");
    //Serial.println(clock.second);
    //Serial.print("min:");
    //Serial.println(clock.minute);
    
    nbSavePoints_total++;
    
    if((clock.year >= 0 && clock.year < 100) &&
       (clock.month > 0 && clock.month <= 12) &&
       (clock.dayOfMonth > 0 && clock.dayOfMonth <= 31) &&
       (clock.second >= 0 && clock.second < 60) &&
       (clock.hour >= 0 && clock.hour < 24) &&
       (clock.minute >= 0 && clock.minute < 60))
    {
      char filename[16];
      
      err_flags &= ~ERR_RTC;
      
      filename[1]='_';
      filename[2]='0' + clock.year/10;
      filename[3]='0' + clock.year%10;
      filename[4]='0' + clock.month/10;
      filename[5]='0' + clock.month%10;
      filename[6]='0' + clock.dayOfMonth/10;
      filename[7]='0' + clock.dayOfMonth%10;
      filename[8]='.';
      filename[9]='l';
      filename[10]='o';
      filename[11]='g';
      filename[12]=0;
      
      err_flags &= ~(ERR_SD_CARD|ERR_EXISTING_DATA);
      lock_mutex=1;
      
      filename[0]='I';
      if (tempIn >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, tempIn);
        
      filename[0]='O';
      if (tempOut >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, tempOut);
        
      filename[0]='T';
      if (temp >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, temp);
        
      filename[0]='1';
      if (tempS1 >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, tempS1);
        
      filename[0]='2';
      if (tempS2 >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, tempS2);
        
      filename[0]='3';
      if (tempS3 >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, tempS3);
      
        
      lock_mutex=0;
      temp_clear=1;
      
      
      filename[0]='P';
      if(cnt_clear)
        err_flags |= addDataPoint(filename, 0);
      else
        err_flags |= addDataPoint(filename, cnt/16);
      
      cnt_clear=1;
      
      if(err_flags&ERR_SD_CARD)
      {
        sdCardErrCounter++;
      }
      else if(err_flags)
        nbSavePoints_err++;
      else
      {
        nbSavePoints_ok++;
      }
    }
    else
      err_rtc=1;
  }
  else
    err_rtc=1;
  
  if(err_rtc)
  {
    rtcErrCounter++;
    err_flags |= ERR_RTC;
  }
    
  handle_serial();
  delay(1100);
}

int addDataPoint(char* filename, int value)
{
  uint8_t new_file=0;

  if(!SD.begin(chipSelect))
    return ERR_SD_CARD;
  
  File dataFile = SD.open(filename, FILE_WRITE);
  //Serial.println(filename);
  
  if(!dataFile)
    return ERR_SD_CARD;
  else
  {
    uint8_t buffer[5+4+1]="\r\nxxh:???";
    int filesize;
    uint8_t offset, last_minute;
    
    filesize = dataFile.size();
    if(filesize == 0)
      new_file = 1;
    
    //Serial.print("File size:");
    //Serial.println(filesize);
          
    if(filesize > 2+3+clock.hour*(2+3+4*60)+clock.minute*4)
    {
      dataFile.close();
      return ERR_EXISTING_DATA;
    }
    
    for(int i=filesize/(2+3+4*60); i<=clock.hour; i++)
    {
      buffer[2]='0'+i/10;
      buffer[3]='0'+i%10;
              
      if(i == filesize/(2+3+4*60))
        offset = filesize % (2+3+4*60);
      else
        offset = 0;
      
      if(offset < 5)
      {
        dataFile.write(buffer+offset, 5-offset);
        offset = 5;
      }
      else if((offset-5) % 4)
      {
        dataFile.write(buffer+5+((offset-5)%4), 4-((offset-5)%4));
        offset += 4-((offset-5)%4);
      }

      if (i==clock.hour)
        last_minute = clock.minute;
      else
        last_minute = 60;
      for(uint8_t j=(offset-5)/4; j<last_minute; j++)
      {
        if(j)
          buffer[5]=',';
        else
          buffer[5]=':';
        dataFile.write(buffer+5, 4);
      }
    }
    if(clock.minute)
      buffer[5]=',';
    else
      buffer[5]=':';

    buffer[6]=int2hexDigit((value>>8)&0x0F);
    buffer[7]=int2hexDigit((value>>4)&0x0F);
    buffer[8]=int2hexDigit(value&0x0F);
    dataFile.write(buffer+5, 4);
    
    //Serial.print("File size:");
    //Serial.println(dataFile.size());
    //nbSavePoints_ok++;

    dataFile.close();
  }

  if(new_file)
  {
    char buffer[16]="xxLIST.log";

    buffer[0] = filename[0];
    buffer[1] = filename[1];
    
    File dataFileList = SD.open(buffer, FILE_WRITE);

    if(!dataFileList)
      return ERR_SD_CARD;
    else
    {
      uint8_t buffer2[10];
      
      for(uint8_t i=0; i<8; i++)
        buffer2[i] = filename[i];
      buffer2[8] = '\r';
      buffer2[9] = '\n';
      dataFileList.write(buffer2, 10);
      dataFileList.close();
    }
  }

  return 0;
}

