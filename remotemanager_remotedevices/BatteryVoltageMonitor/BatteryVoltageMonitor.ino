/*
  Analog input, analog output, serial output
 
 Reads an analog input pin, maps the result to a range from 0 to 255
 and uses the result to set the pulsewidth modulation (PWM) of an output pin.
 Also prints the results to the serial monitor.
 
 The circuit:
 * potentiometer connected to analog pin 0.
   Center pin of the potentiometer goes to the analog pin.
   side pins of the potentiometer go to +5V and ground
 * LED connected from digital pin 9 to ground
 
 created 29 Dec. 2008
 modified 9 Apr 2012
 by Tom Igoe
 
 This example code is in the public domain.
 
 */

#define NUMBER_OF_RELAY_SHIELD 3
#define MAX_CMD_LENGTH 16

// These constants won't change.  They're used to give names
// to the pins used:
const int analogInPin = A0;  // Analog input pin that the potentiometer is attached to
const int analogOutPin = 9; // Analog output pin that the LED is attached to

const int relayShieldPin[NUMBER_OF_RELAY_SHIELD] = {5,6,7};

int sensorValue = 0;        // value read from the pot
char cmd[MAX_CMD_LENGTH];
int cmdLength = 0;   // for incoming serial data

void setup() {
  // initialize serial communications at 115200 bps:
  Serial.begin(115200);
  
  analogReference(EXTERNAL);
  
  for(int i=0; i<NUMBER_OF_RELAY_SHIELD; i++)
  {
    digitalWrite(relayShieldPin[i], LOW);
    pinMode(relayShieldPin[i], OUTPUT);
  }
}

void loop() {
  
  if (Serial.available() > 0) {
    cmdLength = Serial.readBytesUntil('\r', cmd, MAX_CMD_LENGTH);

    if(cmdLength == 0)
      Serial.println("E01");
    else if(cmdLength == MAX_CMD_LENGTH)
      Serial.println("E02");
    else if(cmdLength == 4 && !strncmp_P(cmd, PSTR("PING"), cmdLength))
      Serial.println("p");
    else if(cmdLength == 6 && !strncmp_P(cmd, PSTR("STATUS"), cmdLength))
      Serial.println("e0"); //no detectable error
    else if(cmdLength == 8 && !strncmp_P(cmd, PSTR("READ_ALL"), cmdLength))
    {
      int measuredVoltages[NUMBER_OF_RELAY_SHIELD*4+1];
      
      delay(100);               // wait for 200
      //mesure the total voltage
      sensorValue = analogRead(A4);
      measuredVoltages[NUMBER_OF_RELAY_SHIELD*4] = map(sensorValue, 0, 1023, 0, 365); //330*11.05/10 = 365
      
      for(int i=0; i<NUMBER_OF_RELAY_SHIELD; i++)
      {
        digitalWrite(relayShieldPin[i], HIGH); //switch on relay to measure voltages on capacitor pins
        
        delay(200);               // wait for 200
      
        // read the analog in value:
        sensorValue = analogRead(A0);
        // map it to the range of the analog out:
        measuredVoltages[i*4] = map(sensorValue, 0, 1023, 0, 330);
        
        // read the analog in value:
        sensorValue = analogRead(A1);
        // map it to the range of the analog out:
        measuredVoltages[i*4+1] = map(sensorValue, 0, 1023, 0, 330);
        
        // read the analog in value:
        sensorValue = analogRead(A2);
        // map it to the range of the analog out:
        measuredVoltages[i*4+2] = map(sensorValue, 0, 1023, 0, 330);
        
        // read the analog in value:
        sensorValue = analogRead(A3);
        // map it to the range of the analog out:
        measuredVoltages[i*4+3] = map(sensorValue, 0, 1023, 0, 330);
        
        digitalWrite(relayShieldPin[i], LOW);
      }
      
      for(int i=0; i<NUMBER_OF_RELAY_SHIELD*4+1; i++)
      {
        // print the results to the serial monitor:
        if(measuredVoltages[i] < 100)
          Serial.print("0");
        if(measuredVoltages[i] < 10)
          Serial.print("0");
        Serial.println(measuredVoltages[i]);
      }
      Serial.print(F("\r\n"));
    }
    else
      Serial.println("E09");
  }
}
