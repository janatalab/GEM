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


// Sound-related constants
#define MUTE_SOUND 1000
#define UNMUTE_SOUND 1001

// Response-related constants
#define NO_RESPONSE -32000


//
// GEM Control constants
// 
#define GEM_START 1
#define GEM_STOP 0
#define GEM_MAX_SLAVES 4
#define GEM_REQUEST_ACK 1
#define GEM_HANDSHAKE_TIMEOUT 5
#define GEM_WRITE_DUR_MS
#define GEM_SERIAL_BAUDRATE 115200

// Duration (ms) of interrupt pin pulses
#define GEM_WRITE_DUR_MS 1

#define GEM_START_EXP 0xff    //255
#define GEM_STOP_EXP 0xfe     //254
#define GEM_QUERY_STATE 0xfd  //253

#define GEM_TAP_RESET 0

// 
// Metronome-related constants
//
#define GEM_METRONOME_HEURISTIC_AVERAGE 1
#define GEM_METRONOME_ALPHA 0
#define GEM_METRONOME_TEMPO 1


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
