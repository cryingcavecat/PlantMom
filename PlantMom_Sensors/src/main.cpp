#include <Arduino.h>
#include <secrets.h>
#include <WiFi.h>
#include <PubSubClient.h>

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

int lightRelayPin = 25;
int pumpRelayPin = 26;


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
  if (state == "on"){
    digitalWrite(lightRelayPin,HIGH);
  } else if (state == "off"){
     digitalWrite(lightRelayPin,LOW);
  }
}

void pumpWater(float time){
  Serial.print("Pumping water for:");
  Serial.println(time);
  if (time > 0){
    digitalWrite(lightRelayPin,HIGH);
    Serial.println("Starting Pumping");
    delay(time);
    digitalWrite(lightRelayPin,LOW);
    Serial.println("Done Pumping");
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
 
  Serial.println();
  toggleLight("on");
   //reading light values
  lightVal = analogRead(lightPin);
  Serial.print("Light Value = ");
  Serial.println(lightVal);
  lightAdjVolt = lightVal * (3.3/1024);
  Serial.print("lightAdjVolt = ");
  Serial.println(lightAdjVolt);
  client.publish("sensors/light", String(lightAdjVolt).c_str(), true);


  //reading moisture values
  moistureVal = analogRead(moisturePin);
  Serial.print("Moisture Value = ");
  Serial.println(moistureVal);
  client.publish("sensors/moisture", String(moistureVal).c_str(), true);
  delay(5000);
}


