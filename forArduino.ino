#include <SoftwareSerial.h>

extern volatile unsigned long timer0_millis;
unsigned long new_value = 0;
unsigned long timeSet;
const int relayPin = 3;
int flag = 0;
char nomer[11][12]; 
SoftwareSerial mySerial(4, 5); 

void setup() {
    Serial.begin(9600); 
    pinMode(relayPin, OUTPUT);
    mySerial.begin(9600);
    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    if (Serial.available()) {
        String inputString = Serial.readStringUntil('\n');
        
        // Удаляем лишние символы (фигурные скобки)
        inputString.replace("[", ""); 
        inputString.replace("]", "");  
        inputString.trim(); 
        
        // Разделяем строку на числа
        int index = 0;
        char* token = strtok((char*)inputString.c_str(), ",");
        
        while (token != NULL && index < 11) {
            strncpy(nomer[index], token, 12); 
            nomer[index][11] = '\0'; 
            token = strtok(NULL, ",");
            index++;
        }
    }

    char input[12] = {'0','0','0','0','0','0','0','0','0','0','0', '\0'};
    if (mySerial.available()) {
        int i = 0;
        flag = 1;
        
        while (mySerial.available() && i < 11) {
            char x = mySerial.read();
            Serial.print(x);
            delay(5); 
            input[i] = x; 
            i++;
        }
        input[i] = '\0'; 
        Serial.print("Input from QR scanner: ");
        Serial.println(input);

        for(int g = 1; g < 10; g++) { 
            Serial.print("Comparing: ");
            Serial.print(nomer[g]);
            Serial.print(" with ");
            Serial.println(input);

                for (int h = 1; h < strlen(nomer[g]) - 1; h++) { 
                    if (nomer[g][h] != input[h]) { 
                        flag = 0;
                        break;
                    }
                }
            }
 timeSet = millis();
        }


            if (flag) {
        digitalWrite(relayPin, HIGH);
        digitalWrite(LED_BUILTIN, HIGH);
        if (millis() - timeSet > 3000) {
            digitalWrite(LED_BUILTIN, LOW); 
            Serial.print('y');
            digitalWrite(relayPin, LOW);
            flag = 0;
        }
    } 
    } 



