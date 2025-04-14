#define USE_ARDUINO_INTERRUPTS true
#include <PulseSensorPlayground.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// I2C LCD ekran için adres ve boyutlar
#define I2C_ADDR 0x27  // (Bazı ekranlarda 0x3F olabilir)
#define SCREEN_WIDTH 20
#define SCREEN_HEIGHT 4

LiquidCrystal_I2C lcd(I2C_ADDR, SCREEN_WIDTH, SCREEN_HEIGHT);

const int PulseWire = A0;
const int LED13 = 13;
int Threshold = 510;

PulseSensorPlayground pulseSensor;  // Nesneyi oluşturduk

void setup() {
    Serial.begin(9600);
    
    pulseSensor.analogInput(PulseWire);
    pulseSensor.blinkOnPulse(LED13);
    pulseSensor.setThreshold(Threshold);

    // LCD başlatma
    lcd.init();
    lcd.backlight();
    lcd.setCursor(2, 0);
    lcd.print("Nabız Ölçümü");
    
    if (pulseSensor.begin()) {
        Serial.println("OK");  // Python kodunda kontrol amaçlı
    } else {
        Serial.println("ERROR");
    }

    delay(2000);
    lcd.clear();

    // Başlangıç ekranı
    lcd.setCursor(4, 1);
    lcd.print("Nabziniz:");
}

void loop() {
    if (pulseSensor.sawStartOfBeat()) {
        int nabiz = pulseSensor.getBeatsPerMinute();
        
        lcd.clear();
        lcd.setCursor(2, 1);
        lcd.print("Nabziniz:");
        lcd.setCursor(10, 2);
        lcd.print(nabiz);
        lcd.setCursor(14, 2);
        lcd.print(" BPM");

        Serial.println(nabiz);  // Sadece BPM değeri gönderiyoruz
    }

    delay(20);
}