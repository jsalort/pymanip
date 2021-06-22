const size_t bufsize = 128;
char string_buffer[bufsize];
  
void setup() {
  int i;
  
  /*
   * On utilise les pins digitales de 2 à 13 comme générateur de fonction.
   * On les met dès le départ en OUTPUT.
   */
  for (i=2; i<=13; i++) {
    pinMode(i, OUTPUT);
  }

  /*
   * On utilise la LED_BUILTIN comme indicateur (allumée lorsqu'un fonction est en cours
   * d'exécution).
   */
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  /*
   * Communication série
   */
  Serial.begin(9600);
  Serial.println("GBF & Scope on Arduino version 20210622");
}

void single_pulse_generator_us(const int pin_num, const int n_pulses, const unsigned long delay_us) {
  /*
   * La fonction delayMicroseconds n'est fiable que si delay_us < 16383.
   * Donc on utilise cette version pour les delays < 16 ms.
   */
  unsigned long start_time_us, start_time_ms, duration_ms;
  unsigned long written_pulses = 0ul, adjusted_delay_us;
  float avg_sample_rate;
  char str_temp[10];
  
  snprintf(string_buffer, bufsize, "single_pulse_generator_us STARTED %d %d %ul", pin_num, n_pulses, delay_us);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delayMicroseconds(delay_us/2);
  start_time_ms = millis();
  start_time_us = micros();
  while (written_pulses < n_pulses) {
    adjusted_delay_us = (written_pulses+1ul)*delay_us - (micros() - start_time_us);
    digitalWrite(pin_num, HIGH);
    delayMicroseconds(adjusted_delay_us/2ul);
    digitalWrite(pin_num, LOW);
    delayMicroseconds(adjusted_delay_us/2ul);
    written_pulses++;
  }
  duration_ms = millis() - start_time_ms;
  avg_sample_rate = (1000.0 * written_pulses) / float(duration_ms);
  dtostrf(avg_sample_rate, 6, 1, str_temp);
  if (duration_ms < 32000) {
    snprintf(string_buffer, bufsize, "%d pulses written in %d ms (average sample rate %s Hz).", int(written_pulses), int(duration_ms), str_temp);
  } else {
    snprintf(string_buffer, bufsize, "%d pulses written in %d s (average sample rate %s Hz).", int(written_pulses), int(duration_ms/1000), str_temp);
  }
  Serial.println(string_buffer);
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("single_pulse_generator FINISHED");
}

void single_pulse_generator_ms(const int pin_num, const int n_pulses, const unsigned long delay_ms) {
  /*
   * À utiliser si le délai >= 16 ms.
   */
  unsigned long start_time_ms, duration_ms;
  unsigned long written_pulses = 0ul, adjusted_delay_ms;
  float avg_sample_rate;
  char str_temp[10];
  
  snprintf(string_buffer, bufsize, "single_pulse_generator_ms STARTED %d %d %ul", pin_num, n_pulses, delay_ms);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delay(delay_ms/2);
  start_time_ms = millis();
  while (written_pulses < n_pulses) {
    adjusted_delay_ms = (written_pulses+1ul)*delay_ms - (millis() - start_time_ms);
    digitalWrite(pin_num, HIGH);
    delay(adjusted_delay_ms/2ul);
    digitalWrite(pin_num, LOW);
    delay(adjusted_delay_ms/2ul);
    written_pulses++;
  }
  duration_ms = millis() - start_time_ms;
  avg_sample_rate = (1000.0 * written_pulses) / float(duration_ms);
  snprintf(string_buffer, bufsize, "%d pulses written in %d s (average sample rate %s Hz).", int(written_pulses), int(duration_ms/1000), str_temp);
  Serial.println(string_buffer);
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("single_pulse_generator FINISHED");
}

void continuous_pulse_generator_us(const int pin_num, const unsigned long delay_us) {
  /*
   * Attention: seulement si delay_us < 16383.
   */
  unsigned long start_time_us, start_time_ms, duration_ms;
  unsigned long written_pulses = 0ul, adjusted_delay_us;
  float avg_sample_rate;
  char str_temp[10];
  
  snprintf(string_buffer, bufsize, "continuous_pulse_generator_us STARTED %d %ul", pin_num, delay_us);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delayMicroseconds(delay_us/2);
  start_time_ms = millis();
  start_time_us = micros();
  while (!Serial.available()) {
    adjusted_delay_us = (written_pulses+1l)*delay_us - (micros() - start_time_us);
    digitalWrite(pin_num, HIGH);
    delayMicroseconds(adjusted_delay_us/2);
    digitalWrite(pin_num, LOW);
    delayMicroseconds(adjusted_delay_us/2);
    written_pulses++;
  }
  duration_ms = millis() - start_time_ms;
  avg_sample_rate = (1000.0 * written_pulses) / int(duration_ms);
  dtostrf(avg_sample_rate, 6, 1, str_temp);
  snprintf(string_buffer, bufsize, "%d pulses written in %d s (average sample rate %s Hz).", int(written_pulses), int(duration_ms/1000), str_temp);
  Serial.println(string_buffer);
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("continuous_pulse_generator FINISHED");
}

void continuous_pulse_generator_ms(const int pin_num, const unsigned long delay_ms) {
  /*
   * Attention: seulement si delay_us < 16383.
   */
  unsigned long start_time_ms, duration_ms;
  unsigned long written_pulses = 0ul, adjusted_delay_ms;
  float avg_sample_rate;
  char str_temp[10];
  
  snprintf(string_buffer, bufsize, "continuous_pulse_generator_ms STARTED %d %ul", pin_num, delay_ms);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delay(delay_ms/2);
  start_time_ms = millis();
  while (!Serial.available()) {
    adjusted_delay_ms = (written_pulses+1l)*delay_ms - (millis() - start_time_ms);
    digitalWrite(pin_num, HIGH);
    delay(adjusted_delay_ms/2);
    digitalWrite(pin_num, LOW);
    delay(adjusted_delay_ms/2);
    written_pulses++;
  }
  duration_ms = millis() - start_time_ms;
  avg_sample_rate = (1000.0 * written_pulses) / float(duration_ms);
  dtostrf(avg_sample_rate, 6, 1, str_temp);
  snprintf(string_buffer, bufsize, "%d pulses written in %d s (average sample rate %s Hz).", int(written_pulses), int(duration_ms/1000), str_temp);
  Serial.println(string_buffer);
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("continuous_pulse_generator FINISHED");
}

void read_voltage_window(int pin_num, const size_t n_values, float trigger_level, int delay_us) {
  float data[n_values];
  int read_values = 0;
  bool trigged = false;
  char str_temp[10];
  unsigned long start_time_us, start_time_ms, duration_ms;
  float avg_sample_rate;
  
  dtostrf(trigger_level, 5, 3, str_temp);
  snprintf(string_buffer, bufsize, "read_voltage_window STARTED %d %d %s %d", pin_num, n_values, str_temp, delay_us);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  while (read_values < n_values) {
    float val = analogRead(pin_num)*5.0/1023;
    if ((!trigged) && (val >= trigger_level)) {
      trigged = true;
      start_time_ms = millis();
      start_time_us = micros();
    }
    if (trigged) {
      data[read_values++] = val;
      delayMicroseconds(((unsigned long)read_values)*((unsigned long)delay_us) - (micros() - start_time_us));
    } else {
      if (delay_us < 1000) {
        delayMicroseconds(delay_us); 
      } else {
        delayMicroseconds(1000);
      }
    }
    if (Serial.available()) {
      // Abort
      Serial.read();
      return;
    }
  }
  duration_ms = millis() - start_time_ms;
  avg_sample_rate = (1000.0 * read_values) / int(duration_ms);
  dtostrf(avg_sample_rate, 6, 1, str_temp);
  snprintf(string_buffer, bufsize, "%d values read in %d ms (average sample rate %s Hz).", read_values, int(duration_ms), str_temp);
  Serial.println(string_buffer);
  for (read_values = 0; read_values < n_values; read_values++) {
    dtostrf(data[read_values], 5, 3, str_temp);
    Serial.println(str_temp);
  }
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("read_voltage_window FINISHED");
}

int run_command(int argc, char *argv[]) {
  if (argc > 0) {
    if (strcmp(argv[0], "pulse") == 0) {
      if (argc == 4) {
        int pin_num = atoi(argv[1]);
        int n_pulses = atoi(argv[2]);
        unsigned long delay_us = atol(argv[3]);
        if (delay_us < 16383) {
          single_pulse_generator_us(pin_num, n_pulses, delay_us);
        } else {
          single_pulse_generator_ms(pin_num, n_pulses, delay_us / 1000);
        }
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: pulse pin_num n_pulses delay_us.");
      }
    } 
    else if (strcmp(argv[0], "continuous") == 0) {
      if (argc == 3) {
          int pin_num = atoi(argv[1]);
          unsigned long delay_us = atol(argv[2]);
          if (delay_us < 16383) {
            continuous_pulse_generator_us(pin_num, delay_us);
          } else {
            continuous_pulse_generator_ms(pin_num, delay_us/1000);
          }
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: continuous pin_num delay_us."); 
      }
    } 
    else if (strcmp(argv[0], "read_analog") == 0) {
      if (argc == 5) {
        int pin_num = atoi(argv[1]);
        const unsigned int n_values = atoi(argv[2]);
        float trigger_level = atof(argv[3]);
        int delay_us = atoi(argv[4]);
        read_voltage_window(pin_num, n_values, trigger_level, delay_us);
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: read_analog pin_num n_values trigger_level delay_us.");
      }
    }
    else if (strcmp(argv[0], "write_digital") == 0) {
      if (argc == 3) {
        int pin_num = atoi(argv[1]);
        const int val = atoi(argv[2]);
        if (val == 0) {
          digitalWrite(pin_num, LOW);
          snprintf(string_buffer, bufsize, "write_digital FINISHED %d LOW", pin_num);
          Serial.println(string_buffer);
        } else if (val == 1) {
          digitalWrite(pin_num, HIGH);
          snprintf(string_buffer, bufsize, "write_digital FINISHED %d HIGH", pin_num);
          Serial.println(string_buffer);
        } else {
          Serial.println("ERROR. Wrong value for write_digital.");
        }
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: write_digital pin_num value. value = 0 or 1.");
      }
    }
    else {
      snprintf(string_buffer, bufsize, "ERROR. Unknown command '%s'.", argv[0]);
      Serial.println(string_buffer);
    }
    
  }
}

void loop() {
  int communication_index = 0;
  char **ap, *argv[10], *inputstring = &string_buffer[0];
  int argc = 0;

  // Wait for data
  while (!Serial.available()) {
    delay(1);
  }

  // Read line
  string_buffer[0] = 0;
  while (1) {
    char inByte;
    if (Serial.available()) {
      inByte = Serial.read();
      string_buffer[communication_index++] = inByte;
      if (communication_index > bufsize) {
        communication_index = 0;
      }
    } else {
      delay(1);
      continue;
    }
    if ((inByte == '\n') || (inByte == 0)) {
      string_buffer[communication_index-1] = 0;
      break;
    }
  }

  Serial.println(string_buffer);
  
  for (ap = argv; (*ap = strsep(&inputstring, " \t")) != NULL;) {
      if (**ap != '\0') {
        argc++;
        if (++ap >= &argv[10]) {
          break;
        }
     }
   }
   run_command(argc, argv);
}
