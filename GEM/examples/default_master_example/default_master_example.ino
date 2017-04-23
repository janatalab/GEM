#include <GEMmaster.h>

GEMmaster master;

void setup(){
  
  Serial.begin(9600);
  master.getGemInfo(); // optional function for user setup and debugging
   
}

void loop(){

  master.runGEM(); // run the groove machine
  
}
