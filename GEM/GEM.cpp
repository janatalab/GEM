///////////////////////////////////////////////////////////////////

/*
Implementation of adaptive metronome class


*/

///////////////////////////////////////////////////////////////////
#include "Arduino.h"
#include "GEMConstants.h"
#include "GEM.h"
#include "GEMreport.h"
#include "Lock.h"
///////////////////////////////////////////////////////////////////

///////////////////////////////////////////////////////////////////
////////// METRONOME CLASS //////////
Metronome::Metronome() : next(0)
{
    // Specify default values for the metronome

    // alpha is the proportion of adaptivity from metronome
    // (0 = no adaptation; 1 = overly adaptive (unhelpful))
    // See Fairhurst, Janata, & Keller, 2012
    // default alpha value
    alpha = 0.3;

    // NOTE: LF - is bpm stuff necessary? - can do on python side. metronome
    //doesn't need to know about it.
    // high threshold for metronome BPM
    // Note: this cannot be higher than 300 BPM or it crashes
    BPMmax = 150;

    // low threshold for metronome BPM
    BPMmin = 30;

    // initial ticking bpm
    BPMinit = 120;

    //NOTE: <ioi> member variable depends on <bpm> (also member), so we make
    //a setter function for bpm so ioi always get updated -SA 20170706
    setTempo(BPMinit);

    played = false;

}

void Metronome::setTempo(int new_bpm)
{
    bpm = new_bpm;
    setIOI();
}

//this should only be called from setTempo, to change ioi use this -SA 20170706
void Metronome::setIOI()
{
    //NOTE: this performs integer division, so if floor was intended
    //that should be used (not a cast) if precision is important
    //-SA 20170702
    ioi = floor(60000 / bpm);
}

int Metronome::scheduleNext(volatile int asynchArray[], volatile bool isActive[],
    uint8_t numSlaves, uint8_t heuristic)
{
    int asynchSum = 0;
    int numResponse = 0;
    int asynchAdjust;

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
        if (numResponse > 0) {
            asynchAdjust = floor(asynchSum / numResponse * alpha);
        }
        else {
            asynchAdjust = 0;
        }

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
