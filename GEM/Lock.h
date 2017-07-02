#ifndef GEM_LOCK_H_
#define GEM_LOCK_H_

#include "Arduino.h"

/* =============================================================================
NOTE: A <ScopedVolatileLock> is used to ensure unique access to a volatile
variable *OUTSIDE* of an ISR (ISRs are automatically disabled within ISRs). I.E. one should be used when writing to a variable that is read within an ISR *OR* reading from a variable that is written to within an ISR. The lock works by
saving the state of the status register and disabling interupts in the
constructor, then resetting the status register upon destruction.
WARNING: the behavior of this class depends entirely on scope, so it
should be used witin the most narrow scope possible. See example usage in
Metronome::scheduleNext() in GEM.cpp
-SA 20170702
============================================================================= */
class ScopedVolatileLock
{
public:
    //the state of SREG is saved witin the intialization
    ScopedVolatileLock() : _sreg(SREG)
    {
        //turn interupts off
        cli();
    }
    ~ScopedVolatileLock()
    {
        //reset the stats register to whatever it was (on or off...) when this
        //object goes out of scope
        SREG = _sreg;
    }
private:
    byte _sreg;
};
/* ========================================================================== */
#endif //GEM_LOCK_H_
