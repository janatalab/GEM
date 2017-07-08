// GEMsound.cpp

// TODO: 19Mar2017 Need better, more dynamic indexing scheme. 
//                 As of right now, we're just looking for a file named 1.WAV

// 18Mar2017 Petr Janata - started code

#include "Arduino.h"
#include "GEMreport.h"
#include "GEMsound.h"

// GEMSound constructor
GEMSound::GEMSound(){

  // Get a connection to the reporting interface
  GEMReport r;

}

// Public wrapper for playSoundFile()
void GEMSound::play(void){
  playSoundFile(_file);
}

// setup the SD Card
void GEMSound::setupSDCard(void){
  // Basic info message
  r.infostr("Setting up SD card");

  // WAVE HC card init
  if (!card.init()) r.error(ERR_WAVEHC_CARD_INIT);

  // enable optimized read - some cards may timeout
  card.partialBlockRead(true);

  // initialize volume
  // This holds the information for the partition on the card
  if (!vol.init(card)) r.error(ERR_WAVEHC_CARD_INIT);

  // This holds the information for the volumes root directory
  if (!root.openRoot(vol)) r.error(ERR_WAVEHC_ROOT_OPEN);
}

void GEMSound::indexFiles(void){

  // char name[10];
  // int i = 0; // TODO: Global variable?

  // // copy flash string to RAM
  // strcpy_P(name, PSTR("x.WAV"));

  // // Make file name
  // name[0] = fileLetter[i];

  // // Open file by name
  // if (!_file.open(root, name)) error("open by name");

  // // Save file's index (byte offset of directory entry divided by entry size)
  // // Current position is just after entry so subtract one.
  // fileIndex[i] = root.readPosition()/32 - 1;

}

// loads sound file identified by name from SD Card
FatReader GEMSound::loadByName(char *str){
  // PgmPrintln("Index files"); // indexes files
  // _index = index;
  //indexFiles();

  // open sound file by index
//  if (!file.open(root, fileIndex[index])) err("open by index");
 //if (!_file.open(root, _index)) r.error(ERR_WAVEHC_OPEN_BY_INDEX);

  // Open file by name
  if (!_file.open(root, str)) r.error(ERR_WAVEHC_OPEN_BY_NAME);
  if (!wave.create(_file)) r.error(ERR_WAVEHC_WAVE_CREATE);

  return _file;
}

// creates and plays a wave object
void GEMSound::playSoundFile(FatReader _file){

	// create a Wave
	// 18Mar2017 PJ - see about needing to create it only once
	// and then subsequently just play (and rewind if necessary)
	//if (!wave.create(_file)) r.error(ERR_WAVEHC_WAVE_CREATE);

  // stop playback in case we're playing back
  if (wave.isplaying) {
    wave.stop();
  }

  // Make sure we're at the beginning
  wave.seek(0);

	// start playback
	wave.play();

	// while(wave.isplaying){
	// // Serial.println("SUP FOO");
	// }
	// wave.stop();

 //  // Rewind
 //  wave.seek(0);
  
}
