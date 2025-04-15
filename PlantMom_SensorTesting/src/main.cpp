#include <Arduino.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>


#define SEALEVELPRESSURE_HPA (1010) // Change this to your local sea level pressure (hPa)
 
Adafruit_BMP280 bme;

int lightPin = A0;

int lightVal = 0;
float voltage = 0;
// put function declarations here:
int myFunction(int, int);

void setup() {
 
  Serial.begin(115200);
  delay(1000);
  if (!bme.begin(0x76)) {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    while (1);
  }
}

void loop() {
  Serial.print("Temperature = ");
  Serial.print(bme.readTemperature());
  Serial.println(" *C");
 
  Serial.print("Pressure = ");
  Serial.print(bme.readPressure() / 100.0F); // hPa to Pa conversion
  Serial.println(" hPa");
 
  Serial.print("Approx. Altitude = ");
  Serial.print(bme.readAltitude(SEALEVELPRESSURE_HPA));
  Serial.println(" m");
 
  Serial.println();
  lightVal = analogRead(lightPin);

  Serial.println("Light Value = ");
  Serial.print(lightVal);
  voltage = lightVal * (3.3/1024);
  Serial.println("Voltage = ");
  Serial.print(voltage);
  delay(2000);
}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}