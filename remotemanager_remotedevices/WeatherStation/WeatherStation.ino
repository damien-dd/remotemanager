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
#include <LiquidCrystal.h>
#include <DallasTemperature.h>
#include "DS1307.h"


#define MAX_CMD_LENGTH 48

#define ERR_EXISTING_DATA 1
#define ERR_SD_CARD 2
#define ERR_RTC 4
/*
 The circuit:
 * LCD RS pin to digital pin 9
 * LCD Enable pin to digital pin 8
 * LCD D4 pin to digital pin A0
 * LCD D5 pin to digital pin A1
 * LCD D6 pin to digital pin A2
 * LCD D7 pin to digital pin A3
 * LCD R/W pin to ground
 * 10K resistor:
 * ends to +5V and ground
 * wiper to LCD VO pin (pin 3)
 */
LiquidCrystal lcd(9, 8, A0, A1, A2, A3);

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


// We use 1bus per sensor
#define ONE_WIRE_BUS1 2

// Setup oneWire instances to communicate with OneWire devices
OneWire oneWire1(ONE_WIRE_BUS1);

// Pass oneWire references to Dallas Temperature. 
DallasTemperature sensor(&oneWire1);

volatile unsigned char err_flags = 0;
volatile unsigned char ovf_flags = 0;
volatile unsigned char err_rtc = 0;


volatile byte lock_mutex = 0;
volatile byte temp_clear = 0;
volatile int temp = -1;


volatile unsigned int nbSavePoints_total=0;
volatile unsigned int nbSavePoints_err=0;
volatile unsigned int nbSavePoints_ok=0;
volatile unsigned int sdCardErrCounter=0;
volatile unsigned int rtcErrCounter=0;
volatile unsigned int sensorErrCounter=0;

volatile int8_t timeout;

volatile int16_t temperature=-1;

volatile uint8_t lcd_mutex=0;


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
  static uint32_t temp_sum=0;
  static uint8_t temp_nb=0, cnt;
  
  cnt++;
  timeout--;
    
  if (sensor.getResolutionByIndex(0) != TEMPERATURE_PRECISION)
    initTemperatureSensor(&sensor);
  else
    temperature=sensor.getTempRawByIndex(0)+64*16;
  
  if(temperature < 0)
    sensorErrCounter++;
  
  if(temp_clear)
  {
    temp_sum=0;
    temp_nb=0;
    
    temp_clear=0;
  }
  
  if(!lcd_mutex)
  {
    // set the cursor to column 0, line 1
    // (note: line 1 is the second row, since counting begins with 0):
    lcd.setCursor(1, 0);
    if (cnt&1)
      lcd.print(':');
    else
      lcd.print(' ');
      
    lcd.setCursor(2, 0);
  }
  
  if(temperature > 0)
  {
    temp_sum+=temperature;
    temp_nb++;
    if(!lock_mutex)
        temp=temp_sum/temp_nb;
        
    if(!lcd_mutex)
    {
      lcd.print((float)(temperature-64*16)/16.0, 1);
      lcd.print((char)223);
      lcd.print("C   ");
    }
  }
  else if(!lock_mutex)
  {
    if(!lcd_mutex)
      lcd.print("???");
    temp=-1;
  }

  //start conversions on all sensors
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
 
  
  pinMode(6, OUTPUT);
  analogWrite(6, 90);
  
  clock.begin();
  clock.startClock();
  
  // initialize temperature sensors
  initTemperatureSensor(&sensor);
  
  // set up the LCD's number of columns and rows: 
  lcd.begin(16, 2);
  // Print a message to the LCD.
  lcd.print("T:");
  
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
      Serial.print(F("E01"));
    else if(cmdLength == MAX_CMD_LENGTH)
      Serial.print(F("E02"));
    else if(cmdLength == 4 && !strncmp_P(cmd, PSTR("PING"), cmdLength))
    {
      
      Serial.print("p");
    }
    else if(cmdLength == 8 && !strncmp_P(cmd, PSTR("READ_ALL"), cmdLength))
    {
      Serial.print(F("T: "));
      if(temperature > 0)
        Serial.print(float(temperature-64*16)/16, 1);
      else
        Serial.print(F("???"));
      Serial.println(F("°C"));
    }
    else if(cmdLength == 6 && !strncmp_P(cmd, PSTR("STATUS"), cmdLength))
    {
      Serial.print("e");
      Serial.print(err_flags|ovf_flags, HEX);
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
        Serial.print(F("E20"));
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
        Serial.print(F("E04"));
    }
    else if(cmdLength == 13 && !strncmp_P(cmd, PSTR("READ_ALL"), cmdLength))
    {
      Serial.print(F("Temperature:"));
      Serial.println(temp);
    }
    else if(cmdLength == 12 && !strncmp_P(cmd, PSTR("READ_ERR_CNT"), cmdLength))
    {
      Serial.print(F("Save point:"));
      Serial.println(nbSavePoints_err);
      Serial.print(F("SD:"));
      Serial.println(sdCardErrCounter);
      Serial.print(F("RTC:"));
      Serial.println(rtcErrCounter);
      Serial.print(F("Sensor:"));
      Serial.println(sensorErrCounter);
      Serial.print(F("Success:"));
      Serial.println(nbSavePoints_ok);
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
          Serial.print(F("E11"));
      }
      else
        Serial.print(F("E10"));
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
              else if(str[1] >= '0' && str[1] <= '9' && str[2] >= '0' && str[2] <= '9')
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
                
                if(((str[0]>='0' && str[0]<='9') || (str[0]>='A' && str[0]<='F')) &&
                   ((str[1]>='0' && str[1]<='9') || (str[1]>='A' && str[1]<='F')) &&
                   ((str[2]>='0' && str[2]<='9') || (str[2]>='A' && str[2]<='F')))
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
          Serial.print(F("E11"));
      }
      else
        Serial.print(F("E10"));
    }
    else
      Serial.print(F("E03"));
  }
}

void loop()
{
  err_rtc=0;
  clock.getTime();

  if(clock.second >= 0 && clock.second < 60)
  {
    lcd_mutex=1;
    lcd.setCursor(1, 1);
    if(!(clock.dayOfMonth/10))
      lcd.print('0');
    lcd.print(clock.dayOfMonth);
    lcd.print('/');
    if(!(clock.month/10))
      lcd.print('0');
    lcd.print(clock.month);
    lcd.print('/');
    if(!(clock.year/10))
      lcd.print('0');
    lcd.print(clock.year);
    lcd.print(' ');
    if(!(clock.hour/10))
      lcd.print('0');
    lcd.print(clock.hour);
    lcd.print(':');
    if(!(clock.minute/10))
      lcd.print('0');
    lcd.print(clock.minute);
    lcd_mutex=0;
    
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
      
      err_flags &= ~(ERR_SD_CARD|ERR_EXISTING_DATA|0x10);
      lock_mutex=1;
        
      filename[0]='T';
      if (temp >= 0 && !temp_clear)
        err_flags |= addDataPoint(filename, temp);
      else
        err_flags = 0x10;
        
      lock_mutex=0;
      temp_clear=1;
      
      if(err_flags&ERR_SD_CARD)
      {
        lcd_mutex=1;
        lcd.setCursor(11, 0);
        lcd.print("SDerr");
        lcd_mutex=0;
        sdCardErrCounter++;
      }
      else if(err_flags)
        nbSavePoints_err++;
      else
      {
        lcd_mutex=1;
        lcd.setCursor(11, 0);
        lcd.print(" OK  ");
        lcd_mutex=0;
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
    
    lcd_mutex=1;
    lcd.setCursor(1, 1);
    lcd.print("??/??/?? ??:??");
    lcd_mutex=0;
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

