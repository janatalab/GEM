// This file contains all of the constants for:
// - the GEM library
// - the associated Arduino sketches that utilize the library
// - the python code that controls GEM experiments

// 20170703 - LF converted one byte constants to hex, reorganized a bit,
// commented out unused constants.

#ifndef GEMCONSTANTS_H_
#define GEMCONSTANTS_H_

// #define DEBUG
#undef DEBUG

/* -----------------------------------------------------------------------------
NOTE: I've changed the constants system to use a more structured organization
following Petr's request and Lauren's initial reorganization. This may be a
little too restrictive, but it has some nice features as well. The system is as
follows:
    Each code is 1-byte, the high 4-bits define the "family" or "scope" (I
    prefer using "family" as it doesn't have any other technical meaning that
    I'm aware of) and the low 4-bits define the specific type. This gives us 16
    unique values (i.e. types) for each family. If that isn't enough it can be
    changed pretty easily so (e.g.) each family has 32 types etc. As of now the
    break down of the high 4-bits assignment is:
        0x0*: control (state related) constants
        0x1*: metronome constants (parameter codes etc.)
        0x2*: error constants
        0x3*: sound related constants
        0xf*: DTP format constants
The final section of constants contain constants with non-arbitrary values
(i.e. durations, counts, etc). These are written as integers to reflect that
fact, as they obviously can't follow the family system.

The primary motivation for this chage is 1) Petr's request (and it makes sense),
and 2) if the ECC is going to be setting parameters via Serial IO (e.g. tell
the master what alpha value to use for the following run) then we need some
kind of a state system so the master knows when we are in vs. between runs
(i.e. when to allow parameters to be changed etc.) Feedback is welcome.
-SA 20170706
----------------------------------------------------------------------------- */

/* -----------------------------------------------------------------------------
GEM Control constants (0x0* = 0 - 15)
----------------------------------------------------------------------------- */
#define GEM_STOP         0x00  //0
#define GEM_START        0x01  //1
#define GEM_REQUEST_ACK  0x02  //2

//the "idle" state, in which parameters can be changed and error/debug
//messages can be exchanged
#define GEM_STATE_IDLE  0x03  //3

//the "run" state, in which GEM_START, GEM_STOP, MUTE and UNMUTE are the only
//valid messages from ECC->master and only data is returned from master
#define GEM_STATE_RUN   0x04  //4

/* -----------------------------------------------------------------------------
Metronome related constants (0x1* = 16 - 31)
----------------------------------------------------------------------------- */
// NOTE: the heuristic should be 1-byte, (256 options seem sufficient) if that
// changes make sure to change Metronome::scheduleNext signature
// NOTE: these will be used in same loop as GEM_START etc. so need to be unique
// values - LF 20170703
#define GEM_METRONOME_HEURISTIC_AVERAGE 0x10  //16
#define GEM_METRONOME_ALPHA             0x11  //17
#define GEM_METRONOME_TEMPO             0x12  //18

/* -----------------------------------------------------------------------------
Error handling related constants (0x2* = 32 - 47)
----------------------------------------------------------------------------- */
// ETP -> error transfer protocol
// TODO: integrate this
#define GEM_ERROR                0x20  //32
#define ERR_WAVEHC_CARD_INIT     0x21  //33
#define ERR_WAVEHC_VOL_INIT      0x22  //34
#define ERR_WAVEHC_ROOT_OPEN     0x23  //35
#define ERR_WAVEHC_OPEN_BY_NAME  0x24  //36
#define ERR_WAVEHC_OPEN_BY_INDEX 0x25  //37
#define ERR_WAVEHC_WAVE_CREATE   0x26  //38

/* -----------------------------------------------------------------------------
Sound related constants (0x3* = 48 - 71)
----------------------------------------------------------------------------- */
//NOTE: these might be considered control / "state" constants too, so it might
//make sense to move then to the contol family
#define MUTE_SOUND   0x30 //48
#define UNMUTE_SOUND 0x31 //49

/* -----------------------------------------------------------------------------
DTP identifiers (DTP -> data transfer protocol: 0xf* = 240 - 255)
----------------------------------------------------------------------------- */
// transfer only raw data: metronome time & asynchronies
#define GEM_DTP_RAW 0xf0 //240

/* -----------------------------------------------------------------------------
Miscellaneous constants for which the value is non-arbitrary. These are written
as ints to indicate this, but often are used in a single-byte context...
----------------------------------------------------------------------------- */

//Slave-related constants
#define GEM_MAX_SLAVES 4
#define NO_RESPONSE   -32000
// #define GEM_TAP_RESET 0 // not used

//Performance related constants
#define GEM_HANDSHAKE_TIMEOUT 5
#define GEM_SERIAL_BAUDRATE 115200

// Duration (ms) of interrupt pin pulses
#define GEM_WRITE_DUR_MS 1

/* -------------------------------------------------------------------------- */
// NOTE: everything below was for other branch LF + SA were working on. Can be
// commented out for v0.0.0

// ECC->Arduino data transfer protocol
// 2-byte header:
//    byte 1: recipient (id of master or slave)
//    byte 2: parameter id (see below)
// N-byte message (i.e. data) as a '\n' terminated string

// #define GEM_START_EXP 0xff    //255
// #define GEM_STOP_EXP 0xfe     //254
// #define GEM_QUERY_STATE 0xfd  //253

//arduino ids
// #define GEM_MASTER_ID 0x00
// #define GEM_SLAVE1_ID 0x01
// #define GEM_SLAVE2_ID 0x02
// #define GEM_SLAVE3_ID 0x03
// #define GEM_SLAVE4_ID 0x04
//
// //parameter ids
// #define GEM_WAV_FILE 0x02
// #define GEM_NUM_SLAVES_REQ 0x03

#endif
