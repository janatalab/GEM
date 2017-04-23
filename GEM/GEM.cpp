///////////////////////////////////////////////////////////////////

/*
  GEM.cpp - Library of utilities used in GEM projects
  Wisam Reid, Lauren Fink, David Miranda
  December 2017

*/

// 19Mar2017 Petr Janata - migrated sound playing stuff into GEMsound; added Metronome class

///////////////////////////////////////////////////////////////////
#include "Arduino.h"
#include "GEM.h"
#include "GEMreport.h"
///////////////////////////////////////////////////////////////////

#define DEBUG 0

// GEM constructor
GEM::GEM(){

}


// Read I2C from Master when data is received
// void GEM::receiveI2CEvent(int byteCount) {

//   Serial.print("Time: ");           // time label, does not get recorded in string

//   char WireChar = 'X';              // records incoming characters to this variable
//   int TapLatency;
//   String TapTime;

//   TapTime = "";                     // reads serial port by character and stores tap latency value
//   TapLatency = 900;                 // takes TapTime and converts it to an integer for the slave. can be used when beat needs to be moved

//   while (1 < Wire.available() && WireChar != ' ') {  // loops until transmission ends or a space is printed

//     WireChar = Wire.read();         // receive byte as a character

//     Serial.print(WireChar);         // print the character
//     TapTime += WireChar;            // saves characters to a string

//   }

//   long d = Wire.read();             // dummy cause the wire prints 32 for some reason
//   Serial.println("End");            // end of data that we need


//   TapLatency = TapTime.toInt();     // converts incoming characters into the tap time
//   Serial.println(TapLatency);       // print the tap time as an integer

// }


//////////////////////////// Sets/Gets and Prints


// print configuration details
// void GEM::getGemInfo(void){
//     printGemType();
//     printI2CAddress();
//     printPins();
// }


// void GEM::printGemType(void){

//   if (gemType == 1){
//     // low on memory
//     printItln("I am configurd as a slave");
//   }
//   else if (gemType == 2){
//     // low on memory
//     printItln("I am configurd as the master");
//   }
//   else{
//     // low on memory
//     error("Uh oh! Something is wrong. Am I a slave or a master?");
//   }
// }

// void GEM::printPins(void){
//   printIt("FSR Pin: ");
//   Serial.println(FSRpin);
//   printIt("Send Pin: ");
//   Serial.println(sendPin);
// }

// void GEM::printI2CAddress(void){
//     if (gemType == 1){ // print address for slave
//       printIt("I2C Address: ");
//       Serial.println(I2C_Address);
//     }
//     if (gemType == 2){} // skip output for master
// }

// // return the
// int GEM::getI2CAddress(void){
//     return I2C_Address;
// }

///////////////////////////////////////////////////////////////////

////////// METRONOME CLASS //////////
Metronome::Metronome(){
  // Specify default values for the metronome

  // alpha is the proportion of adaptivity from metronome
  // (0 = no adaptation; 1 = overly adaptive (unhelpful))
  // See Fairhurst et al.
  alpha =  .3;

  // high threshold for metronome BPM
  // Note: this cannot be higher than 300 BPM or it crashes
  BPMmax = 150;

  // low threshold for metronome BPM
  BPMmin = 30;

  // initial ticking bpm
  BPMinit = 120;

  bpm = BPMinit;

  ioi = long(60000/bpm);

  played = false;

}

void Metronome::scheduleNext(int asynchArray[], bool isActive[], int numSlaves, int heuristic){
  int asynchSum = 0;
  int numResponse = 0;
  int asynchAdjust;
  //bool DEBUG = 1;

  // Accumulate
  for (int s=0; s < numSlaves; s++){
    if (isActive[s] && (asynchArray[s] != NO_RESPONSE)){
      if (heuristic == MET_HEURISTIC_AVERAGE){
        asynchSum += asynchArray[s];
      }
      numResponse++;
    }
  }

  // Calculate the global adjustment
  if (heuristic == MET_HEURISTIC_AVERAGE){
    asynchAdjust = int(asynchSum/numResponse * alpha);
    if (DEBUG){
      Serial.print("adj: ");
      Serial.println(asynchAdjust);
    }
  }

  // Schedule the next time
  next += ioi + asynchAdjust;

  // Toggle our flags
  played = false;
};
