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

int Metronome::scheduleNext(volatile int asynchArray[], volatile bool isActive[],
    uint8_t numSlaves, uint8_t heuristic)
{
    int asynchSum = 0;
    int numResponse = 0;
    int asynchAdjust;
    //bool DEBUG = 1;

    // Accumulate
    for (uint8_t s = 0; s < numSlaves; s++)
    {
        //NOTE: the global volatile arrays (currAsynch etc.) are passed by
        //address (i.e. are pointers within this function) so we need to
        //protect access to asynchArray just as we would to the globals
        //in fact, a redesign to avoid use of global volatile arrays would
        //really be best as passing them around is pretty dangerous
        //-SA 20170702
        ScopedVolatileLock lock;
        if (isActive[s] && (asynchArray[s] != NO_RESPONSE))
        {
            if (heuristic == GEM_METRONOME_HEURISTIC_AVERAGE)
            {
                asynchSum += asynchArray[s];
            }
            numResponse++;
        }

        //NOTE: <lock> goes out of scope here, allowing interrupts to run after
        //each iteration is complete -SA 20170702
    }

    // Calculate the global adjustment
    if (heuristic == GEM_METRONOME_HEURISTIC_AVERAGE)
    {
        //NOTE: this performes integer division, then promotion,
        // then multiplication, then truncation. If floor() was
        //intended that should be used if precision is important
        //-SA 20170702
        asynchAdjust = (int)(asynchSum / numResponse * alpha);
#ifdef DEBUG
        Serial.print("adj: ");
        Serial.println(asynchAdjust);
#endif
    }

    //NOTE: use of extra {} for ScopedVolatileLock release the
    //<lock> immediatly after Metronome::next is written to
    //-SA 20170702
    {
        ScopedVolatileLock lock;
        // Schedule the next time
        next += ioi + asynchAdjust;
    }

    // Toggle our flags
    played = false;

    return asynchAdjust;
};
