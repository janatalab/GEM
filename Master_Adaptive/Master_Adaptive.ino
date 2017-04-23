//////////////////////// GEM MASTER METRONOME/////////////////////////
//
// 19Mar2017 Petr Janata - Completely refactored previous code to:
//                         1. take into account new components of GEM Library
//                            for handling sounds.
//                         2. use of arrays for slaves instead of repeated chunks of code
//                         3. cleaned up interrupt routine handling
//                         4. fixed and simplified adaptive timing mechanism calculations

// TODO:
// 1. Setting of parameters by Experiment Control Computer (ECC)
// 2. Additional adaptation heuristics that take into account subdivisions

// INCLUDE LIBRARIES //

// Interrupt library
#define EI_ARDUINO_INTERRUPTED_PIN // this will provide info about which pin the interrupt was on
#include <EnableInterrupt.h>

// I2C Communication library
#include <Wire.h>

// GEM stuff, including Metronome class
#include <GEM.h>

//GEMsound object for master
#include <GEMsound.h>

// GEM constants
#include <GEMreport.h>

// DEFINES for compiler
#define DEBUG 0
#define MAX_SLAVES 4
#define HANDSHAKE_TIMEOUT 5

///////////  Global Variables  ///////////
bool TRIAL_RUNNING = false; // this ultimately has to be a variable that is turned off and on by the ECC

// Get a metronome object with default parameters
Metronome met;

// Get ourselves a GEMSound object
char soundName[ ] = "1.WAV";
GEMSound sound;

// Get ourselves a reporting object
GEMReport report;

// Keep track of which slaves are actually connected
bool slaveIsConnected[MAX_SLAVES];
uint8_t currSlave;
uint8_t numSlaves = 0; // actual number of slaves, determined dynamically

//// PINS THAT WE RECEIVE INTERRUPTS ON FROM THE SLAVES
uint8_t recPins[MAX_SLAVES] = {6, 7, 8, 9};

// INTERRUPT FUNCTIONS //
uint8_t currPin;

// Figure out which slave in our slave array we are dealing with
// given the interrupt that was fired
uint8_t indexFromPin(uint8_t thePin){
  for (int s = 0; s < MAX_SLAVES; s++){
    if (recPins[s] == thePin){
      return s;
    }
  }
}

// Slave handshake function //
void slaveHandshake(void) {
  // Make sure the interrupted pin was the one we wanted
  if (arduinoInterruptedPin == currPin){
    slaveIsConnected[currSlave] = true;
    numSlaves++;
  }
}

// TIMING VARIABLES //
// Many of these are contained in the Metronome object
// Variable that contains time of next scheduled metronome event
//unsigned long scheduledMetronomeTime = 0;
unsigned long currentTime;
unsigned long windowEnds = 0;  // Time that the next window ends met.next + met.ioi/2
unsigned long window = 0;

// Create an array of tap times for the current window, 
// relative to the next schedule metronome time
int currAsynch[MAX_SLAVES];

// Tap time registering function that gets attached to the interrupt//
void registerTap(void){
  currAsynch[indexFromPin(arduinoInterruptedPin)] = millis() - met.next;
}

///////////////// ASSIGN DIAGNOSTIC LEDs ////////////////

// flash if interrupt
int LEDPin = A0;
// visual metronome led
int metronomeLED = A1;

////////////////////////////////////////////////////////////
///////////////// ARDUINO Setup() FUNCTION /////////////////
////////////////////////////////////////////////////////////

void setup(){
  // Enable serial communication
  Serial.begin(9600);

  // Enable the Wire interface for I2C communication
  report.infostr("Enabling I2C");
  Wire.begin(); // master does not need address

  // Enable PINs for flashing LEDs
  report.infostr("Enabling diagnostic LEDs");
  pinMode(LEDPin, OUTPUT); // Interrupt
  pinMode(metronomeLED, OUTPUT); // Metronome

  // Check to see which slaves are connected
  report.infostr("Checking for connected slaves");
  for (int s = 0; s < MAX_SLAVES; s++){
    // Get the current pin
    currPin = recPins[s];

    // Copy the current slave to global
    currSlave = s;
    
    // Enable the interrupt on the pin that we're expecting to receive acknowledgement on
    enableInterrupt(currPin, slaveHandshake, RISING);
    
    // Send a message on the I2C bus, asking the slave to pulse the interrupt pin
    Wire.beginTransmission(s+1); // transmit to device #
    Wire.write(GEM_REQUEST_ACK); // sends one byte
    Wire.endTransmission(); // stop transmitting
    delay(HANDSHAKE_TIMEOUT); // give time to do handshake

    // Disable the interrupt
    disableInterrupt(currPin);

    // check whether we successfully had slave communicate on designated pin
    if (slaveIsConnected[currSlave]){
      Serial.print("Found slave using interrupt: ");
      Serial.println(currPin);

      // Attach our desired ISR
      enableInterrupt(currPin, registerTap, RISING);
    } else {
      // flash LED
      digitalWrite(LEDPin, HIGH);
      delay(500);
      digitalWrite(LEDPin, LOW);
    }
  } // for (int s = 0; s < MAX_SLAVES; s++)

  // Report on number of active slaves
  Serial.print("#active slaves: ");
  Serial.println(numSlaves);

  // Initialize the sound card
  sound.setupSDCard();
  
  // Load a sound file
  if (DEBUG) report.infostr("Loading sound file");
  sound.loadByName(soundName);
  if (DEBUG) report.infostr("Done loading sound file");

  Serial.println("Send 1 from console to start");
} // setup()

//////////////////////////////////////////////////////////////////
/////////////// END OF ARDUINO Setup() FUNCTION //////////////////
//////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////
//////////////// ARDUINO Loop() FUNCTION ////////////////
/////////////////////////////////////////////////////////

void loop() {
  // Check whether there is any message from the ECC
  if (Serial.available()){
    int msg = Serial.parseInt();
    switch (msg){
      case GEM_STOP:
        TRIAL_RUNNING = false;
        break;

      case GEM_START:
        TRIAL_RUNNING = true;
        break;

      case MUTE_SOUND:
        for (int s=0; s < MAX_SLAVES; s++){
          if (slaveIsConnected[s]){
            Wire.beginTransmission(s+1); // transmit to device #
            Wire.write(MUTE_SOUND); // sends one byte
            Wire.endTransmission(); // stop transmitting           
          }
        }
        break;

      case UNMUTE_SOUND:
        for (int s=0; s < MAX_SLAVES; s++){
          if (slaveIsConnected[s]){
            Wire.beginTransmission(s+1); // transmit to device #
            Wire.write(UNMUTE_SOUND); // sends one byte
            Wire.endTransmission(); // stop transmitting           
          }
        }
        break;
        
      default:
        Serial.print("Unknown msg: ");
        Serial.println(msg);
    }
  }
  
  if (TRIAL_RUNNING){
    // Get the current time
    currentTime = millis();

    // Did we cross over to a new window?
    // If so, we need to schedule a new metronome event
    if (currentTime >= windowEnds){
        // Catch us up if we have fallen behind
        if ((met.next + met.ioi + met.ioi/2) < currentTime){
          met.next = long(currentTime - met.ioi/2);
        }
 
        // Schedule the next metronome event given our asynchronies, active slaves, and the desired heuristic
        met.scheduleNext(currAsynch, slaveIsConnected, MAX_SLAVES, MET_HEURISTIC_AVERAGE);

        // when does this window end
        windowEnds = met.next + long(met.ioi/2); 

        // reset the current tap times
        for (int s=0; s < MAX_SLAVES; s++){
          currAsynch[s] = NO_RESPONSE;
        }

        // Send data to the ECC

        // Increment our window counter
        window++;

        if (DEBUG) {
          Serial.print("Scheduled ");
          Serial.print(window);
          Serial.print(": ");
          Serial.println(met.next);
        }
    } // if (currentTime >= windowEnds)

    // Check whether we have passed the scheduled metronome time
    if ((currentTime >= met.next) && !met.played){

      if (DEBUG) {
        //Serial.print("Played: ");
        Serial.println(currentTime);
      }
      sound.play(); // play the sound
      
      met.played = true; // flag that it has been played
    }
    
  } // if (TRIAL_RUNNING)

}

/////////////////////////////////////////////////////////////////////
////////////////////////////  Loop() End ////////////////////////////
/////////////////////////////////////////////////////////////////////


