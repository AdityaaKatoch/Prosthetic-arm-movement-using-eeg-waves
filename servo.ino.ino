#include <Servo.h>

Servo myServo;
Servo myServo2;


void setup() {
  Serial.begin(9600);  // Ensure the baud rate matches the Python code
  myServo.attach(9);   // Attach the servo to pin 9
  myServo2.attach(7);
  myServo.write(90);   // Start the servo in a neutral position (90 degrees)
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();  // Read the incoming command ('0' or '1')
    if (command == '0') {
      
          myServo.write(90);
          myServo2.write(0);
          delay(1000);
      
    }
    else if (command == '1') 
    {
      
          myServo.write(0);
          myServo2.write(90);
          delay(1000);
      
     
    }
  }
}
