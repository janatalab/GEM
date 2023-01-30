// GEMsound.cpp

// TODO: 19Mar2017 Need better, more dynamic indexing scheme.
//                 As of right now, we're just looking for a file named 1.WAV

// 18Mar2017 Petr Janata - started code

#include "Arduino.h"
#include "GEMsound.h"

// GEMSound constructor
GEMSound::GEMSound() {}

// Public wrapper for playSoundFile()
void GEMSound::play(void){
  playSoundFile();
}

// setup the SD Card
void GEMSound::setupSDCard(void){

#ifdef DEBUG
  Serial.println(F("Init SD card"));
#endif

  // WAVE HC card init TODO
  // if (!card.init()) r.error(ERR_WAVEHC_CARD_INIT);

  card.init();

  // enable optimized read - some cards may timeout
  card.partialBlockRead(true);

  // initialize volume
  // This holds the information for the partition on the card TODO
  // if (!vol.init(card)) r.error(ERR_WAVEHC_CARD_INIT);

  // This holds the information for the volumes root directory TODO
  // if (!root.openRoot(vol)) r.error(ERR_WAVEHC_ROOT_OPEN);

  vol.init(card);
  root.openRoot(vol);
}

uint8_t GEMSound::numAvailableSounds(void){
  uint8_t numFiles = 0;

  root.rewind();
  while (root.readDir(dirBuf) > 0) {     // read the next file in the directory 
    // skip subdirs . and ..
    // if (dirBuf.name[0] == '.' || DIR_IS_SUBDIR(dirBuf))
    //   continue;
    if (DIR_IS_FILE(dirBuf) && !(dirBuf.name[0] == '_'))
      numFiles++;
  }

  return numFiles;
}

void GEMSound::getSoundNameByIndex(uint8_t s_index){
  uint8_t index = 0;

  // Rewind our directory
  root.rewind();

  while (root.readDir(dirBuf) > 0) {     // read the next file in the directory 
    // skip subdirs . and ..
    // if (dirBuf.name[0] == '.' || DIR_IS_SUBDIR(dirBuf)) 
    //   continue;

    if (DIR_IS_FILE(dirBuf) && !(dirBuf.name[0] == '_')){
      if (index == s_index){
        dirName(dirBuf, name);
        break;
      } else {
        index++;
      }
    }
  }
}

// loads sound file identified by name from SD Card
FatReader GEMSound::loadByName(char *str){
  _file.open(root, str);
  wave.create(_file);

  return _file;
}

// creates and plays a wave object
void GEMSound::playSoundFile(void){

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
