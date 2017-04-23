// GEMerror.cpp
//
// Error reporting interface for GEM

// 19Mar2017 Petr Janata

#include "Arduino.h"
#include "GEMreport.h"

GEMReport::GEMReport() {
	//Serial.begin(9600);
}

void GEMReport::error(int error_code){
	// Transmit the error code via the Serial interface
	Serial.print("Error: ");
	Serial.println(error_code);
};

void GEMReport::infostr(char *str){
	// Transmit the error code via the Serial interface
	Serial.print("Info: ");
	Serial.println(str);
};
