#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "";  // Замените на имя вашей сети
const char* password = "";  // Замените на пароль вашей сети
const char* server = "";  // Замените на IP вашего сервера

void setup() {
    Serial.begin(9600);
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Connected to WiFi");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        WiFiClient client;

        http.begin(client, server);

        int httpCode = http.GET();

        if (httpCode > 0) {
            String payload = http.getString();
            Serial.println("Received data: " + payload);
        } else {
            Serial.printf("Error on HTTP request: %s\n", http.errorToString(httpCode).c_str());
        }
        
        http.end();
    } else {
        Serial.println("WiFi not connected");
    }

    delay(20000);  // Ждем 20 секунд перед следующим запросом
}
