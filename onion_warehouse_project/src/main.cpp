#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHTesp.h>
#include <MQ135.h>
#include <ArduinoJson.h>
#include "config.h"

#define DHT_PIN 4
#define MQ135_PIN 34
#define RELAY_PIN 25

DHTesp dht;
MQ135 mq135 = MQ135(MQ135_PIN);

float temperature = 25.0, humidity = 65.0;
float co2_ppm = 0, nh3_ppm = 0, benzene_ppm = 0, total_ppm = 0;
bool coolerOn = false;

void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  
  dht.setup(DHT_PIN, DHTesp::DHT22);
  delay(1000);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  Serial.print("🧅 Connecting");
  int i = 0;
  while (WiFi.status() != WL_CONNECTED && i++ < 40) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Connected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\n❌ WiFi Failed. Restarting...");
    delay(3000);
    ESP.restart();
  }
}

void sendDataToBackend() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("x-api-key", API_KEY);

    StaticJsonDocument<256> doc;
    doc["temp"] = temperature;
    doc["hum"] = humidity;
    doc["co2"] = (int)co2_ppm;
    doc["nh3"] = (int)nh3_ppm;
    doc["benzene"] = (int)benzene_ppm;
    doc["total"] = (int)total_ppm;
    doc["cooler"] = coolerOn;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpResponseCode = http.POST(requestBody);
    
    if (httpResponseCode > 0) {
      Serial.print("✅ Backend response: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("❌ Error sending data: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("❌ WiFi Disconnected");
  }
}

void loop() {
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 5000) { // Send every 5 seconds
    lastRead = millis();
    
    TempAndHumidity data = dht.getTempAndHumidity();
    if (dht.getStatus() == 0) {
      temperature = data.temperature;
      humidity = data.humidity;
    }
    
    float correctedPPM = mq135.getCorrectedPPM(temperature, humidity);
    
    co2_ppm = correctedPPM * 0.6;
    nh3_ppm = correctedPPM * 0.25;
    benzene_ppm = correctedPPM * 0.15;
    total_ppm = co2_ppm + nh3_ppm + benzene_ppm;
    
    coolerOn = (temperature > 15 || humidity < 65);
    digitalWrite(RELAY_PIN, coolerOn ? LOW : HIGH);
    
    Serial.printf("🧅 T:%.1f H:%.1f | CO2:%.0f NH3:%.0f Ben:%.0f Tot:%.0f C:%s\n", 
                  temperature, humidity, co2_ppm, nh3_ppm, benzene_ppm, total_ppm,
                  coolerOn ? "ON" : "OFF");
    
    sendDataToBackend();
  }
}
