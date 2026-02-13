#include <SoftwareSerial.h>

// ===== SoftwareSerial =====
SoftwareSerial scanner(4, 5);     // QR-сканер RX, TX
SoftwareSerial espSerial(7, 8);   // RX=7 ← ESP TX, TX=8 → ESP RX

// ===== НАСТРОЙКИ =====
const int OUTPUT_PIN = 3;
const int CODE_LEN = 11;
const unsigned long ESP_INTERVAL = 40000;
const unsigned long ESP_LISTEN_TIME = 10000;

// ===== ПЕРЕМЕННЫЕ =====
String storedCode = "";
String scannerCode = "";

unsigned long lastEspCheck = 0;
unsigned long outputStart = 0;
bool outputActive = false;

void setup() {
  Serial.begin(9600);
  scanner.begin(9600);
  espSerial.begin(9600);

  pinMode(OUTPUT_PIN, OUTPUT);
  digitalWrite(OUTPUT_PIN, LOW);

  Serial.println("[SYSTEM] Arduino started");

  requestCodeFromESP();
  lastEspCheck = millis();

  Serial.println("[SYSTEM] Scanner active");
  Serial.println("--------------------------------");
}

void loop() {
  // === периодический запрос к ESP ===
  if (millis() - lastEspCheck >= ESP_INTERVAL) {
    requestCodeFromESP();
    lastEspCheck = millis();
  }

  // === QR-сканер ===
  scanner.listen();

  if (scanner.available()) {
    scannerCode = "";

    while (scanner.available()) {
      char c = scanner.read();
      if (c >= '0' && c <= '9') scannerCode += c;
      delay(5);
    }

    Serial.print("[QR] Read: ");
    Serial.println(scannerCode);
  }

  // === проверка ===
  if (scannerCode.length() == CODE_LEN && storedCode.length() == CODE_LEN) {
    Serial.print("[CHECK] QR:  ");
    Serial.println(scannerCode);
    Serial.print("[CHECK] ESP: ");
    Serial.println(storedCode);

    if (scannerCode == storedCode) {
      Serial.println("[RESULT] ACCESS GRANTED");
      digitalWrite(OUTPUT_PIN, HIGH);
      outputStart = millis();
      outputActive = true;
    } else {
      Serial.println("[RESULT] ACCESS DENIED");
    }

    Serial.println("--------------------------------");
    scannerCode = "";
  }

  // === выключение выхода ===
  if (outputActive && millis() - outputStart >= 5000) {
    digitalWrite(OUTPUT_PIN, LOW);
    outputActive = false;
    Serial.println("[ACTION] OUTPUT_PIN LOW");
  }
}

// =================================================
// ===== ЗАПРОС КОДА У ESP ==========================
// =================================================
void requestCodeFromESP() {
  Serial.println("[ESP] Sending command get-code");

  espSerial.begin(9600);
  espSerial.println("get-code");   // <<< ВАЖНО
  unsigned long start = millis();

  while (millis() - start < ESP_LISTEN_TIME) {
    if (espSerial.available()) {
      String line = espSerial.readStringUntil('\n');
      line.trim();

      Serial.print("[ESP RAW] ");
      Serial.println(line);

      if (line.startsWith("CODE:")) {
        storedCode = line.substring(5);
        storedCode.trim();

        Serial.print("[ESP] Code saved: ");
        Serial.println(storedCode);
        espSerial.end();
        return;
      }
    }
  }
  espSerial.end();
  Serial.println("[ESP] No code received");
}
