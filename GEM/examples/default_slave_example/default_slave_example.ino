#include <GEMslave.h>

GEMslave slave;

void setup(){
  
  Serial.begin(9600);
  slave.getGemInfo(); // optional function for user setup and debugging
   
}

void loop(){

  slave.runGEM(); // run the groove machine
  
}
