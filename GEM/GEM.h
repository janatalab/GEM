///////////////////////////////////////////////////////////////////
  // NOTE: GEM.h is just metronome. Should be renamed GEMMetronome.h
  // Be sure to also rename in GEM.cpp
  // LF 20170703
///////////////////////////////////////////////////////////////////
#ifndef GEM_h
#define GEM_h
///////////////////////////////////////////////////////////////////

class GEM {

  public:
    // constructor
    GEM();
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

    // // NOTE: These are unnecessary. LF - 20170705 - we can do these BPM checks
    // //on python side. Metronome only uses IOI anyway.
    // // // high threshold for metronome BPM
    // // // NOTE: this cannot be higher than 300 BPM or it crashes
    int BPMmax;

    // low threshold for metronome BPM
    int BPMmin;

    // initial ticking bpm
    int BPMinit;

    // Has the sound been played in this window
    bool played;

    // Time of next event
    // NOTE: <next> is accessed within the registerTap() ISR and so needs to be
    // volatile qualified -SA 20170628
    volatile unsigned long next;

    //NOTE: changed numTappers and heuristic to 1-byte as 0-255 seems more than
    //enough for both (both are defines in GEMConstants which is currently
    //included in GEM.cpp so we don't actually need to pass them at all)
    //-SA 20170702
    // Functions
    int scheduleNext(volatile int asynchArray[], volatile bool isActive[],
        uint8_t numTappers, uint8_t heuristic);

    //NOTE: setter/getter methods for ioi and bpm
    void setTempo(int);
    uint16_t getIOI() const { return ioi; };

private:
    void setIOI();

private:
    //NOTE: ioi and bpm are interdependent, so they need to be kept insync, thus
    //we make them private and provide get and set methods as needed
    // -SA 20170706

    // inter-onset-interval (ms) corresponding to bpm
    //NOTE: changed to uint16_t (should always be [0, (2^16)-1])
    uint16_t ioi;

    // current bpm
    int bpm;
};

///////////////////////////////////////////////////////////////////

#endif
