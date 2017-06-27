///////////////////////////////////////////////////////////////////
/*
  GEM.h - Library of utilities used in GEM projects
  Wisam Reid, Lauren Fink, David Miranda
  December 2017
  Released into the public domain.
*/
///////////////////////////////////////////////////////////////////
#ifndef GEM_h
#define GEM_h

//#include "GEMutils.h"

// define various constants
//
// These were moved on 27Jun2017 by PJ to GEMConstants.h
// #define MET_HEURISTIC_AVERAGE 1
// #define GEM_START 1
// #define GEM_STOP 0

///////////////////////////////////////////////////////////////////

class GEM {

  public:
    // constructor
    GEM();

    // Variables

    //////// FUNCTIONS
    void getGemInfo(void);

  protected:

    //////// CLASS VARIABLES
    int gemType;                    // Slave = 1, Master = 2
    int FSRpin;                     // analog pin for FSR input
    int sendPin;                    // sends an interrupt on this pin
    int I2C_Address;                // Unique address for slave boards, set to zero for master

    static void receiveI2CEvent(int byteCount); // must be static to be passed into Wire library function

    void printGemType(void);
    void printI2CAddress(void);
    void printPins(void);
    int getI2CAddress(void);

};

// Define a metronome class to contain various metronome parameters
class Metronome {
public:
    // Constructor
    Metronome();

    // Variables
    // alpha is the proportion of adaptivity from metronome
    // (0 = no adaptation; 1 = overly adaptive (unhelpful))
    // See Fairhurst et al.
    float alpha;

    // high threshold for metronome BPM
    // Note: this cannot be higher than 300 BPM or it crashes
    int BPMmax;

    // low threshold for metronome BPM
    int BPMmin;

    // initial ticking bpm
    int BPMinit;

    // current bpm
    int bpm;

    // inter-onset-interval (ms) corresponding to bpm
    unsigned long ioi; 

    // Has the sound been played in this window
    bool played;

    // Time of next event
    unsigned long next;

    // Functions
    void scheduleNext(int asynchArray[], bool isActive[], int numSlaves, int heuristic);
};

///////////////////////////////////////////////////////////////////

#endif
