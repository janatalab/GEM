// This file contains all of the constants for:
// - the GEM library
// - the associated Arduino sketches that utilize the library
// - the python code that controls GEM experiments

// 20170703 - LF converted one byte constants to hex, reorganized a bit,
// commented out unused constants.

#ifndef GEMCONSTANTS_H_
#define GEMCONSTANTS_H_

// Error handling related constants
#define ERR_WAVEHC_CARD_INIT 0x64 //100
#define ERR_WAVEHC_VOL_INIT 0x65 //101
#define ERR_WAVEHC_ROOT_OPEN 0x66 //102
#define ERR_WAVEHC_OPEN_BY_NAME 0x67 //103
#define ERR_WAVEHC_OPEN_BY_INDEX 0x68// 104
#define ERR_WAVEHC_WAVE_CREATE 0x69// 105

// ETP -> error transfer protocol
// TODO: integrate this
#define GEM_ERR 0x96 //150

// GEM Control constants
#define GEM_STOP 0x00
#define GEM_START 0x01
#define GEM_REQUEST_ACK 0x02

// Slave-related constants
#define GEM_MAX_SLAVES 0x04
#define NO_RESPONSE -32000
#define GEM_TAP_RESET 0x00

// Sound-related constants
#define MUTE_SOUND 0xC8 //200
#define UNMUTE_SOUND 0xC9 //201

// Performance-related constants
#define GEM_HANDSHAKE_TIMEOUT 0x05
#define GEM_SERIAL_BAUDRATE 115200

// Duration (ms) of interrupt pin pulses
#define GEM_WRITE_DUR_MS 0x01

// Metronome-related constants
// NOTE: the heuristic should be 1-byte, (256 options seem sufficient) if that
// changes make sure to change Metronome::scheduleNext signature
// NOTE: these will be used in same loop as GEM_START etc. so need to be unique
// values - LF 20170703
#define GEM_METRONOME_HEURISTIC_AVERAGE 0x01
#define GEM_METRONOME_ALPHA 0x0A //10
#define GEM_METRONOME_TEMPO 0x0B //11

// DTP -> data transfer protocol
// transfer only raw data: metronome time & asynchronies
#define GEM_DTP_RAW 0x00

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
