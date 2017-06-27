#ifndef GEMCONSTANTS_H_
#define GEMCONSTANTS_H_

#define GEM_MAX_SLAVES 4

#define GEM_REQUEST_ACK 1

#define GEM_HANDSHAKE_TIMEOUT 5

#define GEM_TAP_RESET 0

#define GEM_SERIAL_BAUDRATE 115200

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

#define GEM_START_EXP 0xff    //255
#define GEM_STOP_EXP 0xfe     //254
#define GEM_QUERY_STATE 0xfd  //253

//parameter ids
#define GEM_METRONOME_ALPHA 0
#define GEM_METRONOME_TEMPO 1
#define GEM_WAV_FILE 2
#define GEM_NUM_SLAVES_REQ 3

#endif
