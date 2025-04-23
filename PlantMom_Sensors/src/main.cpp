#include <Arduino.h>
#include <secrets.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>


#define SEALEVELPRESSURE_HPA (1021) //Joburg Sea Pressure
 
Adafruit_BMP280 bme;

WiFiClient wifNetwork;
PubSubClient client(wifNetwork);

const char* ssid = WIFI_SSID;
const char* password = WIFI_PASS;
const char* mqtt_user = MQTT_USER;
const char* mqtt_pass = MQTT_PASS;

const char* mqtt_server = "192.168.0.199";

int lightPin = 34;
int moisturePin = 35;


int lightVal = 0;
float lightAdjVolt = 0;
int moistureVal = 0;
float moistureValAdj = 0;

int lightRelayPin = 25;
int pumpRelayPin = 26;

float temperature = 0;

bool printDebugOutput = false;

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      client.subscribe("commands/relay1");
      client.subscribe("commands/relay2");
    }
    Serial.println("Trying to connect to MQTT Broker");
    
    delay(500);
  }
  Serial.println("MQTT Broker Connection Achieved!");
}

void toggleLight(String state){
  Serial.println("Toggle Light Command Received");
  if (state == "on"){
    digitalWrite(lightRelayPin,HIGH);
    client.publish("sensors/feedback", "LIGHT STATE: ON", true);
  } else if (state == "off"){
     digitalWrite(lightRelayPin,LOW);
     client.publish("sensors/feedback", "LIGHT STATE: OFF", true);
  }
}

void pumpWater(float time){
  Serial.print("Pumping water for:");
  Serial.println(time);
  if (time > 0){
    digitalWrite(pumpRelayPin,HIGH);
    Serial.println("Starting Pumping");
    //I need to adjust for ms
    delay(time * 1000);
    digitalWrite(pumpRelayPin,LOW);
    Serial.println("Done Pumping");
    client.publish("sensors/feedback", "DONE PUMPING WATER", true);
  }else{
    Serial.println("Water pumping time error");
  }
}

void callback(char* topic, byte* message, unsigned int length) {
  String msg;
  // Convert the byte array to a String
  for (int i = 0; i < length; i++) {
    msg += (char)message[i];
  }
  
  //debug messages
  Serial.println("Message Received");
  Serial.print("Topic: ");
  Serial.println(topic);
  Serial.print("Message: ");
  Serial.println(msg);
  
  
  if (strcmp(topic, "commands/relay1") == 0) {
    toggleLight(msg);
  } else if (strcmp(topic, "commands/relay2") == 0) {
     pumpWater(msg.toFloat());
  }else{
    Serial.print("Message not defined");
  }
  

}

void setup() {
  Serial.begin(115200);
  pinMode(lightRelayPin, OUTPUT);
  pinMode(pumpRelayPin, OUTPUT);

  if (!bme.begin(0x76)) {
    Serial.println("Could not find a valid BME280 sensor, check wiring!");
    delay(500);
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED){
      Serial.println("Attempting WiFi Connection ...");
     delay(500);
  }
  Serial.println("WiFi Connection Success!");

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  reconnect();

}




void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  
  
  temperature = bme.readTemperature();

  client.publish("sensors/temp", String(temperature).c_str(), true);

   //reading light values
  lightVal = analogRead(lightPin);

  lightAdjVolt = lightVal * (3.3/4095.0);

  client.publish("sensors/light", String(lightAdjVolt).c_str(), true);


  //reading moisture values
  moistureVal = analogRead(moisturePin);

  moistureValAdj = moistureVal * (3.3 / 4095.0); 

  client.publish("sensors/moisture", String(moistureValAdj).c_str(), true);

  if (printDebugOutput){
    Serial.print("Moisture Value = ");
    Serial.println(moistureVal);

    Serial.print("Moisture Value Adj = ");
    Serial.println(moistureValAdj);

    Serial.print("lightAdjVolt = ");
    Serial.println(lightAdjVolt);

    Serial.print("Light Value = ");
    Serial.println(lightVal);

    Serial.print("Temperature = ");
    Serial.print(temperature);
    Serial.println(" C");
  }
  delay(5000);
}


