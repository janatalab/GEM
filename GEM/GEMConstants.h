// This file contains all of the constants for the GEM library and the associated Arduino sketches that utilize the library

#ifndef GEMCONSTANTS_H_
#define GEMCONSTANTS_H_

//
// Error handling related constants
//
#define ERR_WAVEHC_CARD_INIT 100
#define ERR_WAVEHC_VOL_INIT 101
#define ERR_WAVEHC_ROOT_OPEN 102
#define ERR_WAVEHC_OPEN_BY_NAME 103
#define ERR_WAVEHC_OPEN_BY_INDEX 104
#define ERR_WAVEHC_WAVE_CREATE 105

// Response-related constants
#define NO_RESPONSE -32000


//
// GEM Control constants
//
#define GEM_STOP 0x00
#define GEM_START 0x01
#define GEM_REQUEST_ACK 0x02

// Sound-related constants (should be sinlge byte unless there is strong
// reason for multi-byte int)
#define MUTE_SOUND 0x03 //1000
#define UNMUTE_SOUND 0x04 //1001

#define GEM_MAX_SLAVES 4

#define GEM_HANDSHAKE_TIMEOUT 5
#define GEM_SERIAL_BAUDRATE 115200

// Duration (ms) of interrupt pin pulses
#define GEM_WRITE_DUR_MS 1

#define GEM_START_EXP 0xff    //255
#define GEM_STOP_EXP 0xfe     //254
#define GEM_QUERY_STATE 0xfd  //253

#define GEM_TAP_RESET 0x00

//
// Metronome-related constants
//
//NOTE: the heuristic should be 1-byte, (256 options seem sufficient) if that
//changes make sure to change Metronome::scheduleNext signiture
#define GEM_METRONOME_HEURISTIC_AVERAGE 0x01
#define GEM_METRONOME_ALPHA 0x00
#define GEM_METRONOME_TEMPO 0x01

//DTP -> data transfer protocol
//transfer only raw data: metronome time & asynchronies
#define GEM_DTP_RAW 0x00

// ECC->Arduino data transfer protocol
// 2-byte header:
//    byte 1: recipient (id of master or slave)
//    byte 2: parameter id (see below)
// N-byte message (i.e. data) as a '\n' terminated string

//arduino ids
#define GEM_MASTER_ID 0
#define GEM_SLAVE1_ID 1
#define GEM_SLAVE2_ID 2
#define GEM_SLAVE3_ID 3
#define GEM_SLAVE4_ID 4


//parameter ids
#define GEM_WAV_FILE 2
#define GEM_NUM_SLAVES_REQ 3

#endif
