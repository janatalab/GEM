///////////////////////////////////////////////////////////////////

/*
    GEM.cpp - Library of utilities used in GEM projects
    Wisam Reid, Lauren Fink, David Miranda
    December 2017

*/

// 19Mar2017 Petr Janata - migrated sound playing stuff into GEMsound; added Metronome class

///////////////////////////////////////////////////////////////////
#include "Arduino.h"
#include "GEMConstants.h"
#include "GEM.h"
#include "GEMreport.h"
#include "Lock.h"
///////////////////////////////////////////////////////////////////

#define DEBUG 0

// GEM constructor
GEM::GEM() {}

///////////////////////////////////////////////////////////////////
////////// METRONOME CLASS //////////
Metronome::Metronome()
{
    // Specify default values for the metronome

    // alpha is the proportion of adaptivity from metronome
    // (0 = no adaptation; 1 = overly adaptive (unhelpful))
    // See Fairhurst et al.
    alpha = 0.3;

    // high threshold for metronome BPM
    // Note: this cannot be higher than 300 BPM or it crashes
    BPMmax = 150;

    // low threshold for metronome BPM
    BPMmin = 30;

    // initial ticking bpm
    BPMinit = 120;

    bpm = BPMinit;

    //NOTE: this performs integer division, so if floor was intended
    //that should be used (not a cast) if precision is important
    //-SA 20170702
    ioi = (unsigned long)(60000 / bpm);

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
      if (heuristic == GEM_METRONOME_HEURISTIC_AVERAGE){
        asynchSum += asynchArray[s];
      }
      numResponse++;
    }
  }

  // Calculate the global adjustment
  if (heuristic == GEM_METRONOME_HEURISTIC_AVERAGE){
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
