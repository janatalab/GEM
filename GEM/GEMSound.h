/**
    GEMSound class definition
    Encapsulates dealing with SD card and reading / playing wav files
 */

/**
    load a wave file
    play sound
 */
#ifndef GEMSOUND_H_
#define GEMSOUND_H_

#include "GEMError.h"

/* TODO:
    1) we need to get the id from master (i.e. GEMMaster)
*/

class GEMSound {
    GEMSound(GEMError *err) : _err(err), _init(false) {};
    ~GEMSound() {};

    bool isInitialized() { return _init; }

    void setWaveID(uint8_t id)
    {
        _waveFileID = id;
        initialize();
    }

    bool initialize() const ()
    {
        SdReader card;
        FatVolume vol;
        FatReader root;
        FatReader file;

        // set up SD card etc...
        if (_err->checkResult(card.init(), GEM_SD_INIT_ERROR))
        {
            return false;
        }

        // enable optimized read - some cards may timeout
        card.partialBlockRead(true);

        // initialize volume: this holds the information for the partition
        // on the card
        if (_err->checkResult(vol.init(card), GEM_SD_VOL_ERROR))
        {
            return false;
        }

        // this holds the information for the volumes root directory
        if (_err->checkResult(root.openRoot(vol), GEM_SD_OPEN_ERROR))
        {
            return false;
        }

        // there are a maximum of 8 bytes in the file name string:
        //  3 for the file name [0-255]
        //  4 for the ".wav"
        //  1 for null termination
        char waveName[] = {'\0','\0','\0','\0','\0','\0','\0','\0'};
        fillNameBuffer(waveName);

        // open the file for reading wav content
        if (_err->checkResult(file.open(root, waveName), GEM_SD_OPEN_ERROR))
        {
            return false;
        }

        // go ahead and read the wav file
        if (_err->checkResult(_wave.create(file), GEM_WAV_CREATE_ERROR))
        {
            return false;
        }

        _init = true;

        return true;
    }

    void play() const
    {
        // start playback
        _wave.play();

        while(_wave.isplaying)
        {
            //do nothing until the file is done playing
        }
        _wave.stop();

        // Rewind
        _wave.seek(0);
    }

private:
    // fill a pre-accocated buffer with the char representation of the wav-file
    // id number (_waveFileID) and append ".wav"
    void fillNameBuffer(char buffer[])
    {
        uint8_t res;
        uint8_t den = 0x64;
        uint8_t inc = 0;
        for (uint8_t k = 0; k < 3; ++k)
        {
            //once we have the first digit (res > 0) we need to include 0's
            //so that 10 doesn't become 1...
            if (((res = _waveFileID / den) > 0) || inc > 0)
            {
                //note the post-increment (inc++) assignes to location inc
                //and *THEN* increments the value of inc
                buffer[inc++] = (char)(res + 0x30);

                //subtract the decimal representation of the digit we just
                //extracted (so if we extracted the '2' from '25', we now have
                // just 5)
                id -= res * den;
            }
            den /= 0x0a;
        }

        buffer[inc++] = '.';
        buffer[inc++] = 'w';
        buffer[inc++] = 'a';
        buffer[inc++] = 'v';
        buffer[inc++] = '\0';
    }

private:
    bool _init;
    uint8_t _waveFileID;
    WaveHC _wave;     // This is the only wave (audio) object, since we will only play one at a time
    GEMError *_err;   // Object used to report errors
};
#endif
