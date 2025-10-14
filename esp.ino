#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "Keenetic-104";  // Замените на имя вашей сети
const char* password = "Misha310808";  // Замените на пароль вашей сети
const char* server = "http://192.168.1.128:8000/get_numbers";  // Замените на IP вашего сервера

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
        WiFiClient client;  // Создаем объект клиента
        const char* host = "192.168.1.128";  // Замените на IP вашего сервера Flask
        const int port = 8000;              // Порт сервера

        Serial.println("Connecting to server...");

        // Пытаемся подключиться к серверу
        if (client.connect(host, port)) {
            Serial.println("Connected to server!");

            // Отправляем HTTP GET-запрос
            client.println("GET /get_numbers HTTP/1.1");
            client.println("Host: " + String(host));
            client.println("Connection: close");
            client.println();  // Пустая строка - конец заголовков

            // Ждем ответа
            while (client.connected() || client.available()) {
                if (client.available()) {
                    String line = client.readStringUntil('\n');
                    Serial.println(line);  // Выводим ответ построчно
                }
            }

            client.stop();  // Закрываем соединение
            Serial.println("Connection closed");
        } else {
            Serial.println("Connection failed!");
        }
    } else {
        Serial.println("WiFi not connected");
    }

    delay(20000);  // Пауза 20 секунд
}