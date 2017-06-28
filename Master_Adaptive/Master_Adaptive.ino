//////////////////////// GEM MASTER METRONOME/////////////////////////
//
// 19Mar2017 Petr Janata - Completely refactored previous code to:
//  1. take into account new components of GEM Library for handling sounds.
//  2. use of arrays for slaves instead of repeated chunks of code
//  3. cleaned up interrupt routine handling
//  4. fixed and simplified adaptive timing mechanism calculations
//
// 28Jun2017 Scottie Alexander
//  1. Minor refactoring and performance improvements (helper functions,
//     reorganized global declarations etc.)
//  2. Qualified all globals used in ISRs as "volitile", omitting qualifier
//     doesn't guarantee issues, but qualification *SHOULD* guarantee
//     correctness
//  3. Added snippet to send data (metronome tone onset and tap asynchronies)
//     to ECC via Serial (THIS IS UNTESTD)
//  *. All changes *SHOULD* be annoted with "NOTE" and "-SA 20170628"

// TODO:
// 1. Setting of parameters by Experiment Control Computer (ECC)
// 2. Additional adaptation heuristics that take into account subdivisions

// INCLUDE LIBRARIES //

// Interrupt library
#define EI_ARDUINO_INTERRUPTED_PIN // this will provide info about which pin the interrupt was on. This define should remain here
#include <EnableInterrupt.h>

// I2C Communication library
#include <Wire.h>

// GEM stuff, including Metronome class
#include <GEM.h>

//GEMsound object for master
#include <GEMsound.h>

// GEM constants
#include <GEMConstants.h>

// GEM reporting object
#include <GEMreport.h>

// DEFINES for compiler
#define DEBUG 1
//#define MAX_SLAVES 4
//#define HANDSHAKE_TIMEOUT 5

//#define BAUD_RATE 115200

/* =============================================================================
Global variables
============================================================================= */
// this ultimately has to be a variable that is turned off and on by the ECC
bool TRIAL_RUNNING = false;

// Get ourselves a GEMSound object
char soundName[ ] = "1.WAV";
GEMSound sound;

// Get ourselves a reporting object
GEMReport report;

//// PINS THAT WE RECEIVE INTERRUPTS ON FROM THE SLAVES
const uint8_t recPins[GEM_MAX_SLAVES] = {6, 7, 8, 9};

/* =============================================================================
Timing variables
============================================================================= */
// Many of these are contained in the Metronome object
// Variable that contains time of next scheduled metronome event
//unsigned long scheduledMetronomeTime = 0;
unsigned long currentTime;

// Time that the next window ends (met.next + met.ioi/2)
unsigned long windowEnds = 0;
unsigned long window = 0;

/* =============================================================================
Volatile globals
NOTE: all variable that are assigned or accessed within an ISR (but are not
local to that ISR) really *SHOULD* (must?) be qualified as volitile, this is
especially true for multi-byte data
-SA 20170628
============================================================================= */
// actual number of slaves, determined dynamically
volatile uint8_t numSlaves = 0;

// Keep track of which slaves are actually connected
volatile bool slaveIsConnected[GEM_MAX_SLAVES];

// Create an array of tap times for the current window,
// relative to the next schedule metronome time
volatile int currAsynch[GEM_MAX_SLAVES];

volatile uint8_t currSlave;
volatile uint8_t currPin;

/* NOTE: the metronome is a special case, as it's <next> member variable is
   accessed from the registerTap() ISR, so met.next *SHOULD* be volitile
   qualified (and is so, see Metronome source in GEM.h), the whole object
   doesn't need to be qualified though
   -SA 20170628
*/
// Get a metronome object with default parameters
Metronome met;

/* =============================================================================
Diagnostic LEDs
============================================================================= */
// flash if interrupt
int LEDPin = A0;
// visual metronome led
int metronomeLED = A1;

/* =============================================================================
Interupt functions
============================================================================= */
// Figure out which slave in our slave array we are dealing with
// given the interrupt that was fired
uint8_t indexFromPin(uint8_t thePin)
{
    for (uint8_t s = 0; s < GEM_MAX_SLAVES; s++)
    {
        if (recPins[s] == thePin) { return s; }
    }
}
/* -------------------------------------------------------------------------- */
// Slave handshake function //
void slaveHandshake(void)
{
    // Make sure the interrupted pin was the one we wanted
    if (arduinoInterruptedPin == currPin)
    {
        slaveIsConnected[currSlave] = true;
        numSlaves++;
    }
}
/* -------------------------------------------------------------------------- */
// Tap time registering function that gets attached to the interrupt//
void registerTap(void)
{
    //NOTE: async times are relative to the "requested" metronome onset
    //*NOT* the actual onset... -SA 20160628
    //NOTE: the implicit truncation should be safe here (each async will be <
    //32767), but it's still not recommended -SA 20160628
    currAsynch[indexFromPin(arduinoInterruptedPin)] = millis() - met.next;
}
/* =============================================================================
Helper functions
============================================================================= */
inline void wire_write(uint8_t slaveid, uint8_t val)
{
    Wire.beginTransmission(slaveid); // transmit to device #
    Wire.write(val);                 // sends one byte
    Wire.endTransmission();          // stop transmitting
}
/* -------------------------------------------------------------------------- */
void write_to_slaves(uint8_t val)
{
    for (uint8_t k = 0; k < GEM_MAX_SLAVES; ++k)
    {
        if (slaveIsConnected[k])
        {
            wire_write(k+1, val);
        }
    }
}
/* -------------------------------------------------------------------------- */

////////////////////////////////////////////////////////////
///////////////// ARDUINO Setup() FUNCTION /////////////////
////////////////////////////////////////////////////////////

void setup()
{
    // Enable serial communication
    Serial.begin(GEM_SERIAL_BAUDRATE);

    // Enable the Wire interface for I2C communication
    report.infostr("Enabling I2C");
    Wire.begin(); // master does not need address

    // Enable PINs for flashing LEDs
    report.infostr("Enabling diagnostic LEDs");
    pinMode(LEDPin, OUTPUT); // Interrupt
    pinMode(metronomeLED, OUTPUT); // Metronome

    // Check to see which slaves are connected
    report.infostr("Checking for connected slaves");
    for (uint8_t s = 0; s < GEM_MAX_SLAVES; s++)
    {
        // Get the current pin
        currPin = recPins[s];

        // Copy the current slave to global
        currSlave = s;

        // Enable the interrupt on the pin that we're expecting to receive acknowledgement on
        enableInterrupt(currPin, slaveHandshake, RISING);

        // Send a message on the I2C bus, asking the slave to pulse the interrupt pin
        wire_write(s+1, GEM_REQUEST_ACK);
        delay(GEM_HANDSHAKE_TIMEOUT); // give time to do handshake

        // Disable the interrupt
        disableInterrupt(currPin);

        // check whether we successfully had slave communicate on designated pin
        if (slaveIsConnected[currSlave])
        {
            Serial.print("Found slave using interrupt: ");
            Serial.println(currPin);

            // Attach our desired ISR
            enableInterrupt(currPin, registerTap, RISING);
        }
        else
        {
            // flash LED
            digitalWrite(LEDPin, HIGH);
            delay(500);
            digitalWrite(LEDPin, LOW);
        }
    } // for (int s = 0; s < GEM_MAX_SLAVES; s++)

    // Report on number of active slaves
    Serial.print("#active slaves: ");
    Serial.println(numSlaves);

    // Initialize the sound card
    sound.setupSDCard();

    // Load a sound file
    if (DEBUG) { report.infostr("Loading sound file"); }

    sound.loadByName(soundName);

    if (DEBUG) { report.infostr("Done loading sound file"); }

    Serial.println("Send 1 from console to start");
} // setup()

//////////////////////////////////////////////////////////////////
/////////////// END OF ARDUINO Setup() FUNCTION //////////////////
//////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////
//////////////// ARDUINO Loop() FUNCTION ////////////////
/////////////////////////////////////////////////////////

void loop()
{
    // Check whether there is any message from the ECC
    if (Serial.available())
    {
        int msg = Serial.parseInt();
        switch (msg)
        {
            case GEM_STOP:
                TRIAL_RUNNING = false;
                break;

            case GEM_START:
                TRIAL_RUNNING = true;
                break;

            case MUTE_SOUND:
                write_to_slaves(MUTE_SOUND);
                break;

            case UNMUTE_SOUND:
                write_to_slaves(UNMUTE_SOUND);
                break;

            default:
                Serial.print("Unknown msg: ");
                Serial.println(msg);
        }
    }

    if (TRIAL_RUNNING)
    {
        // Get the current time
        currentTime = millis();

        // Did we cross over to a new window?
        // If so, we need to schedule a new metronome event
        if (currentTime >= windowEnds)
        {
            unsigned long last_met = met.next;

            /* NOTE: Not sure about the logic here, met.scheduleNext() appears
               to overwrite the value of met.next that we set here
               -SA 20160628
            */
            // Catch us up if we have fallen behind
            if ((met.next + met.ioi + met.ioi/2) < currentTime)
            {
                //NOTE: not sure what the cast is doing here, met.isi is an
                //unsigned long, so met.ioi/2 will perform integer division
                //yielding an unsigned long (2 gets propoted) and currentTime
                //is an unsigned long too, so the cast is not needed (especially
                // a C-style cast) -SA 20180628
                met.next = long(currentTime - met.ioi/2);
            }

            // Schedule the next metronome event given our asynchronies, active slaves, and the desired heuristic
            met.scheduleNext(currAsynch, slaveIsConnected, GEM_MAX_SLAVES,
                GEM_METRONOME_HEURISTIC_AVERAGE);

            //NOTE: again, the cast is unneeded, see note above -SA 201706828
            // when does this window end
            windowEnds = met.next + long(met.ioi/2);

            // Send data to the ECC
            /*NOTE: each data packet sent to ECC conists of 12 bytes
                -4 for the metronome tone onset (Long on Uno is 4 bytes)
                -8 for the 4 asynchronies (ints on Uno are 2 bytes)
            It's up to the ECC to correctly parse the byte stream
            -SA 20170628
            */

            /*NOTE: we first send the scheduled time of the metronome tone for
            this window, which is what the asynchronies are relative too, see
            note below on Serial.write() shenanigans
            -SA 20170628
            */
            Serial.write((byte *)&last_met, sizeof (unsigned long));

            /*NOTE: Serial can only write a byte at a time (reading the source
            reveals that Serial.write(void* data, int length) just writes
            single bytes in a loop) so to write our array of ints we pass
            <currAsynch> (which is just pointer to the first element) cast to
            byte* and the total number of *BYTES* in the array as the length
            the performance of this data dump should be tested, reading
            some of the technical material that is available makes me suspicious
            that this could be quite slow
            -SA 20170628
            */
            Serial.write((byte *)currAsynch, sizeof (int) * GEM_MAX_SLAVES);

            // reset the current tap times
            for (uint8_t s = 0; s < GEM_MAX_SLAVES; s++)
            {
                currAsynch[s] = NO_RESPONSE;
            }

            // Increment our window counter
            window++;

            if (DEBUG)
            {
                Serial.print("Scheduled ");
                Serial.print(window);
                Serial.print(": ");
                Serial.println(met.next);
            }
        } // if (currentTime >= windowEnds)

        // Check whether we have passed the scheduled metronome time
        if ((currentTime >= met.next) && !met.played)
        {
            if (DEBUG)
            {
                //Serial.print("Played: ");
                Serial.println(currentTime);
            }
            sound.play(); // play the sound

            met.played = true; // flag that it has been played
        }

    } // if (TRIAL_RUNNING)

}

/////////////////////////////////////////////////////////////////////
////////////////////////////    Loop() End ////////////////////////////
/////////////////////////////////////////////////////////////////////
