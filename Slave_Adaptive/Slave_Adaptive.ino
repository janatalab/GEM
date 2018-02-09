//////////////////////// SLAVE TAPPER ////////////////////////
//
// 18Mar2017 - Petr Janata - essentially rebuilding from scratch, keeping some
//             portions of previous code
//
//

//////// INCLUDE LIBRARIES: ////////
// I2C Communication library
#include <Wire.h>

// WaveHC for the Waveshield which handles the loading and playing of the sounds
// 18Mar2017 PJ - we should really create a GEMSound class in GEM.h so that we don't have to
// include this code in both the Master and Slave sketches

// Get all our constants
#include <GEMConstants.h>

// GEM Sound handling stuff
#include <GEMsound.h>

// Reporting interface
#include <GEMreport.h>

////////// DEFINES //////////
// Set the address for this slave.
// This needs to be unique to each tapper (slave), and must therefore
// be changed as each sketch is compiled and uploaded to each slave device
#define ADDRESS 3



// put error messages in flash memory
// 18Mar2017 PJ - we're going to send error codes to the Experiment Control Computer (ECC)
// on the fly, so there is no need to store messages in flash memory.
// We should create a GEMError class that defines all of the constants
//#define error(msg) error_P(PSTR(msg))

/////////////////////////////////

////////////// INITIALIZE GLOBAL VARIABLES  //////////////
// 18Mar2017 PJ - ultimately, the following parameters should be passed in
//                via the Master during initialization:
//  PLAY_TIME - how long should a song play for
//  FSRThresh - the FSR value that should be exceeded in order to register a tap (important for preventing double taps)
//  DEBUG - if True, then this device will send debugging messages via the Serial interface


bool DEBUG = false;

// Variables specifying FSR input and output
// These variables should probably also be stored in an FSR object
// analog pin of FSR
uint8_t FSRpin = 0;

// sends an interrupt on this pin
uint8_t sendPin = 6;


// the FSR value that should be exceeded in order to register a tap
// 20 in Schultz and van Vogt, 10 for more sensitivity
int FSRThresh = 30;

// Timing parameters
uint32_t currTime; // stores time at which the FSR exceeds threshold
uint32_t prevInterruptTime; // stores the time that the last interupt was fired
uint8_t minITI = 50; // the minimum amount of time between the currentTime and prevInterruptTime
                 // must have elapsed before another interrupt is fired

//////// OBJECTS FROM THE WAVEHC LIBRARY: ////////
// We will use the WaveSheild library to play audio
// and handle the SD card

// Get ourselves a GEMSound object
//int soundIndex = 1;  // The index of the sound to load. Should be passed in as a parameter from the ECC
char soundName[ ] = "1.WAV";
GEMSound sound;

bool muteSound = false;

//#define PLAY_TIME 45
/// END OF SOUND STUFF ///

// Get ourselves a reporting object
GEMReport report;

////// FSR Stuff: //////
int currVal = 0; // stores value of FSR current state
bool tapDone = true; // indicates whether a tap was completed

////////////////////////////////////////////////////////////
///////////////// ARDUINO Setup() FUNCTION /////////////////
////////////////////////////////////////////////////////////

void setup() {
  // Set stuff up for serial communication
  Serial.begin(GEM_SERIAL_BAUDRATE);  // begin arduino at [BaudRate]

  //I2C Setup
  Wire.begin(ADDRESS); // join i2c bus with address #
  Wire.onReceive(receiveEvent); // register event

  //PIN SETUP
  pinMode(sendPin, OUTPUT); // set to 6 above
  pinMode(FSRpin, INPUT); // set to 0 above

  // Initialize the sound card
  sound.setupSDCard();

  // Load a sound file
  if (DEBUG) report.infostr("Loading sound file");
  sound.loadByName(soundName);
  if (DEBUG) report.infostr("Done loading sound file");

}
//////////////////////////////////////////////////////////////////
/////////////// END OF ARDUINO Setup() FUNCTION //////////////////
//////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////
//////////////// ARDUINO Loop() FUNCTION ////////////////
/////////////////////////////////////////////////////////

void loop() {
    // read the FSR
    currVal = analogRead(FSRpin);

    // if the value exceeds the designated threshold
    if (currVal >= FSRThresh) {
      // Get the current time
      currTime = millis();

      // Check whether the minimum ITI has elapsed
      if (tapDone && (currTime - prevInterruptTime >= minITI)) {
        // Fire off an interrupt with rising edge
        digitalWrite(sendPin, HIGH);

        // keep the pin high
        delay(GEM_WRITE_DUR_MS);

        // revert pin to 0V
        digitalWrite(sendPin, LOW);

        // play the sound
        if (!muteSound){
          sound.play();
        }

        // Make note of the interrupt time
        prevInterruptTime = currTime;

        // If we just started a tap, it can't be done
        tapDone = false;

        // Send any non-essential messages
        if (DEBUG) Serial.println(currVal); // print the FSR value, for debug
      } // end if (prevInterruptTime - currTime > minITI)
    } else if (!currVal) {
      // If the value of the FSR returns to zero, declare the tap completely done,
      // thus enabling a new tap and associated sound
      if (!tapDone){
        if (DEBUG) Serial.println("");
      }
      tapDone = true;
    } // end if (val >= FSRThresh)
}

/////////////////////////////////////////////////////////////////////
////////////////////////////  Loop() End ////////////////////////////
/////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////
//////////////////////  I2C HELPER /////////////////////
////////////////////////////////////////////////////////

// This is called in the 'Setup()' function above
// receiveEvent is passed to Wire.onReceive() as an argument
void receiveEvent(int howMany){
  int requestCode;

  // Figure out what we need to do based on the message identifier code
  if (DEBUG) Serial.println("Received Wire msg");

  requestCode = Wire.read();
  switch (requestCode)
  {
    case GEM_REQUEST_ACK:
      // Turn around the handshake request by pulsing the digital pin
      if (DEBUG) Serial.println("Performing handshake");

      digitalWrite(sendPin, HIGH);
      delay(GEM_WRITE_DUR_MS);

      // revert pin to 0V
      digitalWrite(sendPin, LOW);
      break;

    case MUTE_SOUND:
      muteSound = true;
      break;

    case UNMUTE_SOUND:
      muteSound = false;
      break;

    default:
      Serial.print("Slave ");
      Serial.print(ADDRESS);
      Serial.print(" unhandled request code: ");
      Serial.println(requestCode);
  }
}

//void receiveEvent(int howMany) {


////////////////////////////////////////////////////////
//////////////////// END I2C HELPER ////////////////////
////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////
//////////////////////////// END Sketch ////////////////////////////
////////////////////////////////////////////////////////////////////
