#include <Arduino.h>

// put function declarations here:
int myFunction(int, int);

int lightPin = 4;
int moisturePin = 35;


int lightVal = 0;
float lightAdjVolt = 0;
int moistureVal = 0;


void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);
}

void loop() {
  // digitalWrite(2,HIGH);// NO1 and COM1 Connected (LED on)
  
  // delay(5000);
  // digitalWrite(2,LOW);// NO1 and COM1 Connected (LED on)
  // delay(60000);

  Serial.println();
  lightVal = analogRead(lightPin);

  Serial.println("Light Value = ");
  Serial.print(lightVal);
  lightAdjVolt = lightVal * (3.3/1024);
  Serial.println("lightAdjVolt = ");
  Serial.print(lightAdjVolt);
  delay(2000);
  moistureVal = analogRead(moisturePin);

  Serial.println("Moisture Value = ");
  Serial.print(moistureVal);
}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}