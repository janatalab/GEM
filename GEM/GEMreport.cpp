// GEMerror.cpp
//
// Error reporting interface for GEM

// 19Mar2017 Petr Janata

#include "Arduino.h"
#include "GEMreport.h"
#include "GEMConstants.h"

GEMReport::GEMReport() {
	//Serial.begin(9600);
}

void GEMReport::error(int error_code){
#ifdef DEBUG
	// Transmit the error code via the Serial interface
	Serial.print("Error: ");
	Serial.println(error_code);
#endif

    // Send error to ECC - LF added 20170703
    //first byte is the data transfer protocol identifier
    Serial.write(GEM_ERR);

    //second byte is the error code from GEM constants
    Serial.write(error_code);
};

void GEMReport::infostr(const char *str){
#ifdef DEBUG
	// Transmit the error code via the Serial interface
	Serial.print("Info: ");
	Serial.println(str);
#endif
};
