#include "ECE140_WIFI.h"
#include "ECE140_MQTT.h"
#include <Wire.h>
#include <Adafruit_BMP085.h>

// MQTT client - using descriptive client ID and topic
// #define CLIENT_ID "esp32-sensors"
// //#define TOPIC_PREFIX "ENTER_SOMETHING_UNIQUE_HERE_THAT_SHOULD_ALSO_MATCH_MAINPY/ece140/sensors"
// #define TOPIC_PREFIX "chynson/ece140/sensors"
const char* clientId = CLIENT_ID;           // Read CLIENT_ID from .env
const char* topicPrefix = TOPIC_PREFIX; 
// ECE140_MQTT mqtt(CLIENT_ID, TOPIC_PREFIX);
ECE140_MQTT mqtt(clientId, topicPrefix);
ECE140_WIFI wifi;
Adafruit_BMP085 bmp;

// WiFi credentials
const char* ucsdUsername = UCSD_USERNAME;
const char* ucsdPassword = UCSD_PASSWORD;
const char* wifiSsid = WIFI_SSID;
const char* nonEnterpriseWifiPassword = NON_ENTERPRISE_WIFI_PASSWORD;

void setup() {
    Serial.begin(115200);

    // Connect to WiFi
    Serial.println(" Connecting to WiFi...");
    wifi.connectToWiFi(wifiSsid, nonEnterpriseWifiPassword);
    // wifi.connectToWPAEnterprise(wifiSsid, ucsdUsername, ucsdPassword);

    // Connect to MQTT broker
    if (!mqtt.connectToBroker(1883)) {
        Serial.println(" Failed to connect to MQTT broker");
    }

    // Initialize BMP085 sensor
    if (!bmp.begin()) {
        Serial.println(" BMP085 sensor not detected. Check wiring!");
        while (1);  // Halt execution if the sensor is missing
    }
    
    Serial.println(" BMP085 sensor initialized!");
}


    
void loop() {
    // mqtt.loop();
    // //Read sensor data
    // //given in the slides
    // //Fill out here
    // int hallValue = hallRead();
    // float temperature = temperatureRead();

    // // sending data
    // String payload = "{\"hall\": " + String(hallValue) + 
    //                  ", \"temperature\": " + String(temperature) + "}";
    // Serial.println("Publishing sensor data");
    // Serial.println(payload);
    // mqtt.publishMessage("readings", payload);
    // delay(2000);
    mqtt.loop();  // Maintain MQTT connection

    // Read temperature and pressure from BMP085 sensor
    float temperature = bmp.readTemperature();
    int32_t pressure = bmp.readPressure();  // Read pressure in Pascals

    // Convert pressure from Pascals to hPa (hectopascals)
    float pressure_hPa = pressure / 100.0;

    //  Correctly formatted JSON string in C++
    String payload = "{\"temperature\": " + String(temperature, 2) + 
                     ", \"pressure\": " + String(pressure_hPa, 2) + "}";

    // Print and publish to MQTT
    Serial.println("📡 Publishing sensor data...");
    Serial.println(payload);

    if (!mqtt.publishMessage("readings", payload)) {
        Serial.println(" MQTT Publish Failed!");
    } else {
        Serial.println(" Data published successfully.");
    }

    delay(2000);  // Read & publish every 2 seconds


}








