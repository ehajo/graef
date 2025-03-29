#pragma once

#include "esphome/core/component.h"
#include "esphome/components/output/binary_output.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/core/hal.h" // Für GPIOPin

namespace esphome {
namespace tm1651 {

class TM1651Component : public Component {
 public:
  void setup() override {
    pin_clk_->pin_mode(gpio::FLAG_OUTPUT);
    pin_dio_->pin_mode(gpio::FLAG_OUTPUT);
    pin_clk_->digital_write(true);
    pin_dio_->digital_write(true);
    sendCommand(0x40); // Datenbefehl: Schreiben an Display
    clearDisplay();
  }

  void loop() override {
    last_keys_ = readKeys(); // Tastenstatus aktualisieren
  }

  void set_pin_clk(GPIOPin *pin) { pin_clk_ = pin; }
  void set_pin_dio(GPIOPin *pin) { pin_dio_ = pin; }
  uint8_t get_keys() const { return last_keys_; }

 protected:
  GPIOPin *pin_clk_;
  GPIOPin *pin_dio_;
  uint8_t last_keys_ = 0; // Speichert den letzten Tastenstatus

  void startTransmission() {
    pin_dio_->digital_write(false);
    delayMicroseconds(5);
  }

  void stopTransmission() {
    pin_dio_->digital_write(false);
    delayMicroseconds(5);
    pin_clk_->digital_write(true);
    delayMicroseconds(5);
    pin_dio_->digital_write(true);
  }

  void sendByte(uint8_t data) {
    for (int i = 0; i < 8; i++) {
      pin_clk_->digital_write(false);
      delayMicroseconds(5);
      pin_dio_->digital_write(data & 0x01);
      delayMicroseconds(5);
      pin_clk_->digital_write(true);
      delayMicroseconds(5);
      data >>= 1;
    }
    // ACK warten
    pin_clk_->digital_write(false);
    pin_dio_->pin_mode(gpio::FLAG_INPUT);
    delayMicroseconds(5);
    pin_clk_->digital_write(true);
    delayMicroseconds(5);
    pin_dio_->pin_mode(gpio::FLAG_OUTPUT);
  }

  void sendCommand(uint8_t cmd) {
    startTransmission();
    sendByte(cmd);
    stopTransmission();
  }

  void sendData(uint8_t addr, uint8_t data) {
    sendCommand(0x44); // Einzeladresse
    startTransmission();
    sendByte(0xC0 | addr); // Adresse (0xC0 = Segment 0, 0xC1 = Segment 1, usw.)
    sendByte(data);        // Daten
    stopTransmission();
  }

  void clearDisplay() {
    sendCommand(0x44);
    for (uint8_t i = 0; i < 8; i++) {
      sendData(i, 0x00);
    }
  }

  uint8_t readKeys() {
    uint8_t keys = 0;
    startTransmission();
    sendByte(0x42); // Befehl zum Lesen der Tasten
    pin_dio_->pin_mode(gpio::FLAG_INPUT);
    for (int i = 0; i < 8; i++) {
      pin_clk_->digital_write(false);
      delayMicroseconds(5);
      keys |= (pin_dio_->digital_read() << i);
      pin_clk_->digital_write(true);
      delayMicroseconds(5);
    }
    stopTransmission();
    pin_dio_->pin_mode(gpio::FLAG_OUTPUT);
    return keys;
  }

  friend class TM1651Output;
  friend class TM1651Sensor;
};

class TM1651Output : public output::BinaryOutput {
 public:
  void set_parent(TM1651Component *parent) { parent_ = parent; }
  void set_segment(uint8_t segment) { segment_ = segment; }

  void write_state(bool state) override {
    if (state) {
      parent_->sendData(segment_, 0x01); // LED an
    } else {
      parent_->sendData(segment_, 0x00); // LED aus
    }
  }

 private:
  TM1651Component *parent_;
  uint8_t segment_;
};

class TM1651Sensor : public binary_sensor::BinarySensor, public PollingComponent {
 public:
  explicit TM1651Sensor(uint32_t update_interval) : PollingComponent(update_interval) {}

  void set_parent(TM1651Component *parent) { parent_ = parent; }
  void set_key_index(uint8_t key_index) { key_index_ = key_index; }

  void update() override {
    uint8_t keys = parent_->get_keys();
    publish_state(keys & (1 << key_index_)); // Zustand der entsprechenden Taste
  }

 private:
  TM1651Component *parent_;
  uint8_t key_index_;
};

}  // namespace tm1651
}  // namespace esphome