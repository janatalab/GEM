#ifndef GEMSLAVEARDUINO_H_
#define GEMSLAVEARDUINO_H_

#include "GEMArduino.h"
/* ========================================================================== */
class GEMSlaveArduino : public GEMArduino
{
public:
    GEMSlaveArduino(uint8_t id, GEMError *err) :
        GEMArduino(uint8_t id, GEMError *err),
        tapRegistered(false)
    {

    };
    /* ---------------------------------------------------------------------- */
    ~GEMSlaveArduino() : {};
    /* ---------------------------------------------------------------------- */
    void initialize() override
    {
        // join as slave
        Wire.begin(_id);
    }
    /* ---------------------------------------------------------------------- */
    //send info to master via I2C protocol (i.e. Wire)
    sendMessageToMaster() {};
    /* ---------------------------------------------------------------------- */
    //check if FSR is > threshold, if !tapRegistered send pulse to master
    //and start playing wav file
    pollFSR() {};
    /* ---------------------------------------------------------------------- */
    //pulse master on interrupt pin
    interruptMaster() {};
    /* ---------------------------------------------------------------------- */
private:
    bool tapRegistered;
};
/* ========================================================================== */
#endif
