#pragma once
#include "esphome.h"
#include <SoftwareSerial.h>

// Diese Komponente überbrückt die Daten zwischen dem Hardware-UART (hw_uart)
// und einem SoftwareSerial-Objekt, das an den gewünschten Pins betrieben wird.
class SoftwareUARTBridge : public Component {
 public:
  // Konstruktor: Hier werden die Pins für den Software-UART und der Zeiger auf den Hardware-UART übergeben.
  SoftwareUARTBridge(uint8_t rx_pin, uint8_t tx_pin, uart::UARTComponent *hw_uart)
      : hw_uart_(hw_uart), soft_serial_(rx_pin, tx_pin) {}

  void setup() override {
    // Starte den SoftwareSerial mit der gleichen Baudrate wie der Hardware-UART.
    soft_serial_.begin(9600);
  }

  void loop() override {
    // Leite Daten vom Hardware-UART zum Software-UART weiter.
    while (hw_uart_->available()) {
      int c = hw_uart_->read();
      if (c >= 0) {
        soft_serial_.write((uint8_t)c);
      }
    }
    // Leite Daten vom Software-UART zurück zum Hardware-UART weiter.
    while (soft_serial_.available()) {
      int c = soft_serial_.read();
      if (c >= 0) {
        hw_uart_->write((uint8_t)c);
      }
    }
  }

 private:
  uart::UARTComponent *hw_uart_;
  SoftwareSerial soft_serial_;
};
