const size_t bufsize = 128;
char string_buffer[bufsize];
  
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  Serial.println("GBF v1");
}

void single_pulse_generator(int pin_num, int n_pulses, int delay_us) {
  snprintf(string_buffer, bufsize, "single_pulse_generator STARTED %d %d %d", pin_num, n_pulses, delay_us);
  Serial.println(string_buffer);
  pinMode(pin_num, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delayMicroseconds(delay_us/2);
  while ((n_pulses--) > 0) {
    digitalWrite(pin_num, HIGH);
    delayMicroseconds(delay_us/2);
    digitalWrite(pin_num, LOW);
    delayMicroseconds(delay_us/2);
  }
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("single_pulse_generator FINISHED");
}

void continuous_pulse_generator(int pin_num, int delay_us) {
  snprintf(string_buffer, bufsize, "continuous_pulse_generator STARTED %d %d", pin_num, delay_us);
  Serial.println(string_buffer);
  pinMode(pin_num, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  digitalWrite(pin_num, LOW);
  delayMicroseconds(delay_us/2);
  while (!Serial.available()) {
    digitalWrite(pin_num, HIGH);
    delayMicroseconds(delay_us/2);
    digitalWrite(pin_num, LOW);
    delayMicroseconds(delay_us/2);
  }
  digitalWrite(pin_num, LOW);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("continuous_pulse_generator FINISHED");
}

void read_voltage_window(int pin_num, const size_t n_values, double trigger_level, int delay_us) {
  double data[n_values];
  int read_values = 0;
  bool trigged = false;
  char str_temp[8];
  
  dtostrf(trigger_level, 4, 2, str_temp);
  snprintf(string_buffer, bufsize, "read_voltage_window STARTED %d %d %s %d", pin_num, n_values, str_temp, delay_us);
  Serial.println(string_buffer);
  digitalWrite(LED_BUILTIN, HIGH);
  while (read_values < n_values) {
    double val = analogRead(pin_num)*5.0/1023;
    if ((!trigged) && (val >= trigger_level)) {
      trigged = true;
    }
    if (trigged) {
      data[read_values++] = val;
      delayMicroseconds(delay_us);
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
  snprintf(string_buffer, bufsize, "%d values read.", read_values);
  Serial.println(string_buffer);
  for (read_values = 0; read_values < n_values; read_values++) {
    dtostrf(data[read_values], 4, 2, str_temp);
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
        int delay_us = atoi(argv[3]);
        single_pulse_generator(pin_num, n_pulses, delay_us);
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: pulse pin_num n_pulses delay_us.");
      }
    } 
    else if (strcmp(argv[0], "continuous") == 0) {
      if (argc == 3) {
          int pin_num = atoi(argv[1]);
          int delay_us = atoi(argv[2]);
          continuous_pulse_generator(pin_num, delay_us);
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: continuous pin_num delay_us."); 
      }
    } 
    else if (strcmp(argv[0], "read_analog") == 0) {
      if (argc == 5) {
        int pin_num = atoi(argv[1]);
        const unsigned int n_values = atoi(argv[2]);
        double trigger_level = atof(argv[3]);
        int delay_us = atoi(argv[4]);
        read_voltage_window(pin_num, n_values, trigger_level, delay_us);
      } else {
        Serial.println("ERROR. Wrong number of arguments. Usage: read_analog pin_num n_values trigger_level delay_us.");
      }
    }
    else {
      snprintf(string_buffer, bufsize, "ERROR. Unknown command %s", argv[0]);
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
      if (communication_index > 255) {
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
