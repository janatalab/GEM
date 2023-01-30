// GEMSound.h
//
// Defines a GEMSound class that utilizes the WaveHC library for the Adafruit Waveshield

// 18Mar2017 Petr Janata - started code

#ifndef GEMSound_h
#define GEMSound_h

// Standard Arduino include
#include "Arduino.h"

// GEM constants
#include "GEMConstants.h"

// WaveHC for the Waveshield
#include "WaveHC.h"

// Waveshield utilites
#include "WaveUtil.h"
   
// Define the GEMSound class
class GEMSound {
public:
  // Constructor
  GEMSound();

  // Functions
  void setupSDCard(void);
  uint8_t numAvailableSounds(void);
  void getSoundNameByIndex(uint8_t index);
  FatReader loadByName(char *str);
  void play(void);
  char name[13];

private:
  int _index;

protected:
  //////// VARIABLES
  SdReader card;  // This object holds the information for the card
  FatVolume vol;  // This holds the information for the partition on the card
  FatReader root; // This holds the information for the volumes root directory
  FatReader _file; // This object represent the WAV file
  WaveHC wave;    // This is the only wave (audio) object, since we will only play one at a time
  dir_t dirBuf;

  //////// FUNCTIONS
  void playSoundFile(void);
}; // end GEMSound

#endif
