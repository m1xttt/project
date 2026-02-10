#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "";
const char* password = "";
const char* server = ""; 

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
        WiFiClient client;
        const char* host = "";  
        const int port = 8000;              

        Serial.println("Connecting to server...");

        if (client.connect(host, port)) {
            Serial.println("Connected to server!");

            client.println("GET /get_numbers HTTP/1.1");
            client.println("Host: " + String(host));
            client.println("Connection: close");
            client.println(); 

            while (client.connected() || client.available()) {
                if (client.available()) {
                    String line = client.readStringUntil('\n');
                    Serial.println(line); 
                }
            }

            client.stop(); 
            Serial.println("Connection closed");
        } else {
            Serial.println("Connection failed!");
        }
    } else {
        Serial.println("WiFi not connected");
    }

    delay(20000);  // Пауза 20 секунд
}
