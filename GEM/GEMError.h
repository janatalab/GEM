/**
    Error reporting utilities for GEM framework
 */
#ifndef GEMERROR_H_
#define GEMERROR_H_

#include "GEMErrorCodes.h"
/* ========================================================================== */
class GEMError {
public:
    /* ---------------------------------------------------------------------- */
    GEMError() : _state(false), _code(GEM_NO_ERROR) {};
    /* ---------------------------------------------------------------------- */
    ~GEMError() {};
    /* ---------------------------------------------------------------------- */
    void reset() { _state = false; };
    /* ---------------------------------------------------------------------- */
    bool hasError() { return _state; };
    /* ---------------------------------------------------------------------- */
    uint16_t getErrorCode()
    {
        if (_state) { return _code; }
        else { return GEM_NO_ERROR; }
    }
    /* ---------------------------------------------------------------------- */
    bool checkResult(bool success, uint16_t code)
    {
        // if the process that we are checking failed, keep the associated
        // error code, otherwise continue with the last error code
        _code = success ? GEM_NO_ERROR : code;

        // _state remains true once the first error has occured
        _state |= !success;

        if (_state) { reportError(); }

        return _state;
    }
    /* ---------------------------------------------------------------------- */
    virtual void reportError() {};
    /* ---------------------------------------------------------------------- */
private:
    bool _state;    // true if an error has been raised
    uint16_t _code; // error code of the *LAST* error that was raised
 };
/* ========================================================================== */
// class GEMMasterError : public GEMError {
//     GEMMasterError() : GEMError() {};
//     ~GEMMasterError() {};
//     void reportError() override
//     {
//         // write to the seril port
//     };
// };
// class GEMSlaveError : public GEMError {
//     GEMSlaveError() : GEMError() {};
//     ~GEMSlaveError() {};
//     void reportError() override
//     {
//         // tell the master that we encountered and error
//     };
// };
#endif
