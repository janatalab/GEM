/**
    Define a base class (GEMArduino) that specifies the basic functionality
    common to all Arduinos (masters and slaves) within the GEM system
 */

/**
    play sound
    handshake?
    set interupts
 */

#ifndef GEMARDUINO_H_
#define GEMARDUINO_H_

#include "Arudino.h"
#include "Wire.h"
#include "GEMSound.h"

/* ========================================================================== */
class GEMArduino {
public:
    /* ---------------------------------------------------------------------- */
    GEMArduino(uint8_t id, GEMError *err) : _id(id), _err(err), _snd(err) {};
    /* ---------------------------------------------------------------------- */
    ~GEMArduino() {};
    /* ---------------------------------------------------------------------- */
    virtual void initialize() const {};
    /* ---------------------------------------------------------------------- */
    bool isInitialized() const
    {
        return _snd.isInitialized();
    }
    /* ---------------------------------------------------------------------- */
    uint8_t getID() const { return _id; }
    /* ---------------------------------------------------------------------- */
    virtual handshake() {};
    /* ---------------------------------------------------------------------- */
    void playSound() const
    {
        _snd.play();
    }
    /* ---------------------------------------------------------------------- */
    void setInterrupt() const
    {
        attachInterrupt(digitalPinToInterrupt(_intrPin), processInterrupt, CHANGE);
    };
    /* ---------------------------------------------------------------------- */
private:
    uint8_t _id;    //unique id number for each Arduino in the GEM system
    GEMSound _snd;  //sound contoller (reads / plays a wav file etc.)
    GEMError *_err; //object used to report errors (this needs to be a pointer
                    //to achieve polymorphism, check constructor syntax...)
};
/* ========================================================================== */
#endif
