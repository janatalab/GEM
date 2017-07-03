// GEMreport.h
//
// Interface for reporting stuff

// 19Mar2017 Petr Janata

#ifndef GEMreport_h
#define GEMreport_h

// These constants should probably be moved to GEMconstants.h
//
// Moved to GEMConstants.h on 27Jun2017 by PJ
// #define ERR_WAVEHC_CARD_INIT 100
// #define ERR_WAVEHC_VOL_INIT 101
// #define ERR_WAVEHC_ROOT_OPEN 102
// #define ERR_WAVEHC_OPEN_BY_NAME 103
// #define ERR_WAVEHC_OPEN_BY_INDEX 104
// #define ERR_WAVEHC_WAVE_CREATE 105
// #define GEM_REQUEST_ACK 1
// #define MUTE_SOUND 1000
// #define UNMUTE_SOUND 1001
// #define NO_RESPONSE -32000

class GEMReport {
public:
	// Constructor
	GEMReport();

	// Functions
	void error(int error_code);
	void infostr(const char *str);
};

#endif
