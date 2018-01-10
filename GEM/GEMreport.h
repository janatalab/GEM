// GEMreport.h
//
// Interface for reporting stuff

// 19Mar2017 Petr Janata

// Don't think we're using this anymore - LF 20180109

#ifndef GEMreport_h
#define GEMreport_h

class GEMReport {
public:
	// Constructor
	GEMReport();

	// Functions
	void error(int error_code);
	void infostr(const char *str);
};

#endif
