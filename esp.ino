  #include <ESP8266WiFi.h>
#include <WiFiClient.h>

// ===== НАСТРОЙКИ =====
const char* ssid     = "arsIk";
const char* password = "volkswagenarteon76";

const char* host = "10.81.147.95";
const int   port = 2612;
const char* path = "/get_numbers";
// =====================

WiFiClient client;

void setup() {
  Serial.begin(9600);
  delay(100);

  Serial.println("[ESP] Boot");

  WiFi.begin(ssid, password);
  Serial.print("[ESP] Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("[ESP] WiFi connected");
  Serial.print("[ESP] IP: ");
  Serial.println(WiFi.localIP());

  Serial.println("[ESP] Waiting for command: get-code");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    Serial.print("[ESP] CMD: ");
    Serial.println(cmd);

    if (cmd == "get-code") {
      requestCodeFromServer();
    }
  }
}

void requestCodeFromServer() {
  Serial.println("[ESP] Connecting to server...");

  if (!client.connect(host, port)) {
    Serial.println("[ESP] Server connection FAILED");
    return;
  }

  Serial.println("[ESP] Server connected");
  Serial.println("[ESP] Sending GET request");

  client.print(
    String("GET ") + path + " HTTP/1.1\r\n" +
    "Host: " + host + "\r\n" +
    "Connection: close\r\n\r\n"
  );

  String payload;
  bool body = false;

  while (client.connected() || client.available()) {
    if (client.available()) {
      String line = client.readStringUntil('\n');
      if (line == "\r") {
        body = true;
      } else if (body) {
        payload += line;
      }
    }
  }

  client.stop();

  Serial.print("[ESP] RAW RESPONSE: ");
  Serial.println(payload);

  // ожидаем формат: [1,2,3,4,5...]
  payload.replace("[", "");
  payload.replace("]", "");
  payload.replace(",", "");
  payload.trim();

  if (payload.length() > 0) {
    Serial.print("CODE:");
    Serial.println(payload);
    Serial.println("[ESP] Code sent");
  } else {
    Serial.println("[ESP] ERROR: empty code");
  }
}
