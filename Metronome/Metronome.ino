//////////////////////// GEM METRONOME/////////////////////////
//
// 19Mar2017 Petr Janata - Completely refactored previous code to:
//  1. take into account new components of GEM Library for handling sounds.
//  2. use of arrays for tappers instead of repeated chunks of code
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

// GEM constants
#include <GEMConstants.h>

// GEM stuff, including Metronome class
#include <GEM.h>

//GEMsound object for metronome
#include <GEMsound.h>

// for ScopedVolatileLock
#include "Lock.h"


#ifdef DEBUG
  #pragma message("DEBUG MODE IS ON")
#endif
// NOTE: if you are sending messages from the Arduino serial monitor for debugging purposes,
// send the family code then value separated by a space. If you send them in succession Arduino
// does not respond properly. - LF 20170706

/* =============================================================================
Global variables
============================================================================= */
// this ultimately has to be a variable that is turned off and on by the ECC
bool TRIAL_RUNNING = false;

//NOTE: the current state that we are in (either IDLE or RUN), we begin in the
//IDLE state to allow ECC to set important parameters (e.g. met.alpha etc.)
//-SA 20170706
uint8_t GEM_CURRENT_STATE = GEM_STATE_IDLE;

// Get ourselves a GEMSound object
// char soundName[ ] = "1.WAV";
char soundName[] = "A2_MAR.WAV";
GEMSound sound;

//// PINS THAT WE RECEIVE INTERRUPTS ON FROM THE TAPPERS
const uint8_t recPins[GEM_MAX_TAPPERS] = {6, 7, 8, 9};

/* =============================================================================
Timing variables
============================================================================= */
// Many of these are contained in the Metronome object
// Variable that contains time of next scheduled metronome event
// unsigned long currentTime;

// Time that the next window ends (met.next + met.getIOI()/2)
unsigned long windowEnds = 0;
uint16_t window = 0x0000;

/* =============================================================================
Volatile globals
NOTE: all variable that are assigned or accessed within an ISR (but are not
local to that ISR) really *SHOULD* (must?) be qualified as volitile, this is
especially true for multi-byte data
-SA 20170628
============================================================================= */
// actual number of tappers, determined dynamically
volatile uint8_t numTappers = 0;

// Keep track of which tappers are actually connected
volatile bool tapperIsConnected[GEM_MAX_TAPPERS];

// Create an array of tap times for the current window,
// relative to the next schedule metronome time
volatile int currAsynch[GEM_MAX_TAPPERS];

volatile uint8_t currTapper;
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
// int LEDPin = A0;
// visual metronome led
// int metronomeLED = A1;

/* =============================================================================
Interupt functions
============================================================================= */
// Figure out which tapper in our tapper array we are dealing with
// given the interrupt that was fired
uint8_t indexFromPin(uint8_t thePin)
{
    for (uint8_t s = 0; s < GEM_MAX_TAPPERS; s++)
    {
        if (recPins[s] == thePin) { return s; }
    }
}
/* -------------------------------------------------------------------------- */
// Tapper handshake function //
void tapperHandshake(void)
{
    // Make sure the interrupted pin was the one we wanted
    if (arduinoInterruptedPin == currPin)
    {
        tapperIsConnected[currTapper] = true;
        numTappers++;
    }
}
/* -------------------------------------------------------------------------- */
// Tap time registering function that gets attached to the interrupt//
void registerTap(void)
{
    //NOTE: async times are relative to the "requested" metronome onset
    //*NOT* the actual onset... -SA 20160628 (also note the truncation)
    currAsynch[indexFromPin(arduinoInterruptedPin)] =  (int)(millis() - met.next);
}
/* =============================================================================
Helper functions
============================================================================= */
inline void wire_write(uint8_t tapperid, uint8_t val)
{
    #ifdef DEBUG
        Serial.print(F("Sending "));
        Serial.print(val);
        Serial.print(F(" to tapper "));
        Serial.println(tapperid);
    #endif

    Wire.beginTransmission(tapperid); // transmit to device #
    Wire.write(val);                 // sends one byte
    Wire.endTransmission();          // stop transmitting

    #ifdef DEBUG
        Serial.println(F("Done transmitting"));
    #endif
}
/* -------------------------------------------------------------------------- */
void write_to_tappers(uint8_t val)
{
    for (uint8_t k = 0; k < GEM_MAX_TAPPERS; ++k)
    {
        //NOTE: this is a bit of a more interesting case, <tapperIsConnected> is
        //a volatile global (set in the tapper handshake ISR) but once it is set
        //it functions effectively as read-only (never gets reset) so
        //'technically' we shouldn't have to protect this with a
        //ScopedVolatileLock as we don't use this function until well after
        //<tapperIsConnected> is set... but we'lll throw one in just to be safe
        //(and performance is not ciritical here) -SA 20170702
        ScopedVolatileLock lock;
        if (tapperIsConnected[k])
        {
            wire_write(k+1, val);
        }

        //NOTE: <lock> is released (goes out of scope) here on each iteration
        //-SA 20170702
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
    Wire.begin(); // metronome does not need address

    // Enable PINs for flashing LEDs
    // pinMode(LEDPin, OUTPUT); // Interrupt
    // pinMode(metronomeLED, OUTPUT); // Metronome

    // Check to see which tappers are connected
    for (uint8_t s = 0; s < GEM_MAX_TAPPERS; s++)
    {

        //NOTE: because the logic here is so procedural (the handshake
        //interrupt can ONLY be called within a very narrowly define window -
        //i.e. between the call to enableInterrupt() and disableInterrupt()) I
        //actually don't think we need to guard access to volatiles (we don't
        //access any volatiles while the ISR in enabled except currPin which is
        //not written to in the ISR). The way this works the exchange could be
        //blocking... but performance here is not critical so I've addded
        //a lock just to be safe -SA 20170702
        {
            ScopedVolatileLock lock;

            // Get the current pin
            currPin = recPins[s];

            // Copy the current tapper to global
            currTapper = s;
        }

        #ifdef DEBUG
            Serial.print(F("Checking tapper "));
            Serial.print(s+1);
            Serial.print(F(" interrupt on pin "));
            Serial.println(currPin);
        #endif

        // Enable the interrupt on the pin that we're expecting to receive acknowledgement on
        enableInterrupt(currPin, tapperHandshake, RISING);

        // Send a message on the I2C bus, asking the tapper to pulse the interrupt pin
        wire_write(s+1, GEM_REQUEST_ACK);
        delay(GEM_HANDSHAKE_TIMEOUT); // give time to do handshake

        // Disable the interrupt
        disableInterrupt(currPin);

        // check whether we successfully had tapper communicate on designated pin
        if (tapperIsConnected[currTapper])
        {
            #ifdef DEBUG
                Serial.print(F("Found tapper: "));
                Serial.println(currPin);
            #endif
            // Attach our desired ISR
            enableInterrupt(currPin, registerTap, RISING);
        }
        else
        {
            #ifdef DEBUG
                Serial.print(F("Tapper "));
                Serial.print(s+1);
                Serial.println(F(" connect failed"));
            #endif
            // flash LED
            // digitalWrite(LEDPin, HIGH);
            // delay(500);
            // digitalWrite(LEDPin, LOW);
        }
    } // for (int s = 0; s < GEM_MAX_TAPPERS; s++)

    #ifdef DEBUG
        // Report on number of active tappers
        Serial.print(F("# tappers: "));
        Serial.println(numTappers);
    #endif

    // Initialize the sound card
    sound.setupSDCard();

    sound.loadByName(soundName);
    #ifdef DEBUG
        Serial.println(F("Playing sound ..."));
        sound.play(); // play the sound
    #endif

    {
        ScopedVolatileLock lock;
        for (uint8_t k = 0; k < GEM_MAX_TAPPERS; ++k)
        {
          currAsynch[k] = NO_RESPONSE;
        }
    }

    #ifdef DEBUG
        Serial.println(F("Send 4 then 1 to start"));
    #endif
} // setup()

//////////////////////////////////////////////////////////////////
/////////////// END OF ARDUINO Setup() FUNCTION //////////////////
//////////////////////////////////////////////////////////////////

/* -----------------------------------------------------------------------------
idle function: called repeatedly from loop() until ECC instructs us to
transition to the RUN state
----------------------------------------------------------------------------- */
void idle()
{
    if (Serial.available())
    {
        //NOTE: in the IDLE state sending data as strings is fine, we just need
        //to keep track of when that is ok on the ECC side (should be simple)
        //we should still use single byte message id codes (i.e. <msg> below)
        // -SA 20170706
        #ifdef DEBUG
            uint8_t msg = (uint8_t)Serial.parseInt();
            Serial.print(F("Rec: "));
            Serial.println(msg);
        #else
            uint8_t msg = (uint8_t)Serial.read();
        #endif

        switch (msg)
        {
            case GEM_STATE_RUN:
                #ifdef DEBUG_SETTINGS
                    Serial.println(F("GEM_STATE_RUN"));
                #endif
                GEM_CURRENT_STATE = GEM_STATE_RUN;
                break;

            case GEM_METRONOME_ALPHA:
                met.alpha = Serial.parseFloat();
                #ifdef DEBUG_SETTINGS
                    Serial.println(F("Alpha: "));
                    Serial.println(met.alpha);
                #endif
                break;

            case GEM_METRONOME_TEMPO:
                //NOTE: met.getIOI() depends on met.bpm (tempo) so we use a
                //setter function to make sure everything that need to be
                //updated gets updated -SA 20170706
                met.setTempo(Serial.parseInt());
                #ifdef DEBUG_SETTINGS
                    Serial.print(F("IOI: "));
                    Serial.println(met.getIOI());
                #endif

                break;

            case LIST_AVAILABLE_SOUNDS:
                {
                    // Get the device whose sounds we are being asked to list
                    uint8_t device; 
                    uint8_t tapper_id; 

                    while (!Serial.available()) delay(10);

                    device = (uint8_t)Serial.read();

                    switch (device){
                        case DEV_TAPPER_1:
                            tapper_id = 1;
                            break;

                        case DEV_TAPPER_2:
                            tapper_id = 2;
                            break;

                        case DEV_TAPPER_3:
                            tapper_id = 3;
                            break;

                        case DEV_TAPPER_4:
                            tapper_id = 4;
                            break;

                        default:
                            tapper_id = 0; // metronome
                    }

                    #ifdef DEBUG_SETTINGS
                        Serial.print(F("Requesting sound list from: "));
                        Serial.println(device);
                    #endif

                    if (tapper_id == 0){
                        #ifdef DEBUG_SETTINGS
                            Serial.print(F("Num available sounds: "));
                            Serial.println(sound.numAvailableSounds());
                        #endif

                        Serial.write(GEM_DTP_SND_LIST);
                        Serial.write(DEV_METRONOME);

                        for (uint8_t s = 0; s < sound.numAvailableSounds(); s++){
                            // Serial.print("Found sound ... ");
                            sound.getSoundNameByIndex(s);
                            // Serial.println(sound.name);
                            Serial.write((char*)sound.name, sizeof(sound.name));
                        }         
                    } else {
                        wire_write(tapper_id, LIST_AVAILABLE_SOUNDS);
                    }

                    // Send a termination code
                    Serial.write(GEM_REQUEST_ACK);

                }

                break;

                // sound.listAvailableSounds()

            //NOTE: potential error reporting system:
            //ECC is requestig error status, send value of global
            //GEM_CURRENT_ERROR -SA 20170706
            //case GEM_ERROR:
            //    Serial.write(GEM_CURRENT_ERROR); //0x00 if no error?
            //    break;
            
            default:
                #ifdef DEBUG_SETTINGS
                    Serial.print(F("Unknown: "));
                    Serial.println(msg);
                #endif
                break;
        }

    }
    else
    {
        delay(10);
    }
}
/* -----------------------------------------------------------------------------
run function: called repeatedly from loop() when in the RUN state (does exactly)
what loop() used to do, moved for organizational clarity
----------------------------------------------------------------------------- */
void run()
{

    // Check whether there is any message from the ECC
    if (Serial.available())
    {
        #ifdef DEBUG
            uint8_t msg = (uint8_t)Serial.parseInt();
            Serial.print(F("Rec: "));
            Serial.println(msg);
        #else
            uint8_t msg = (uint8_t)Serial.read();
        #endif
        switch (msg)
        {
            case GEM_STOP:
                TRIAL_RUNNING = false;
                GEM_CURRENT_STATE = GEM_STATE_IDLE;
                #ifdef DEBUG
                    Serial.println(F("GEM_STATE_IDLE"));
                #endif
                break;

            case GEM_START:
                TRIAL_RUNNING = true;
                #ifdef DEBUG
                    Serial.println(F("GEM_START"));
                #endif
                break;

            case MUTE_SOUND:
                write_to_tappers(MUTE_SOUND);
                break;

            case UNMUTE_SOUND:
                write_to_tappers(UNMUTE_SOUND);
                break;

            default:
                #ifdef DEBUG
                    Serial.print(F("Unknown: "));
                    Serial.println(msg);
                #endif
                break;
        }
    }

    if (TRIAL_RUNNING)
    {
        // Get the current time
        unsigned long currentTime = millis();


        // Did we cross over to a new window?
        // If so, we need to schedule a new metronome event
        if (currentTime >= windowEnds)
        {
            //NOTE: met.next is read (but NOT set) in as ISR so we don't need to
            //protect read-only access -SA 20170702
            unsigned long last_met = met.next;

            // Catch us up if we have fallen behind
            if ((met.next + met.getIOI() + met.getIOI()/2) < currentTime)
            {
                met.next = currentTime - (met.getIOI()/2);
            }

            //NOTE: passing the global volitile array <currAsynch> probably
            //should be avoided if possible, as it is really passing a pointer
            //to a memory location that is written to within an ISR. we can
            //make it "safe" by protecting acces to <currAsynch> within the
            //function (i.e. scheduleNext(), which I have done) but doing it
            //this way makes the sketchiness unobvious -SA 20170702

            // Schedule the next metronome event given our asynchronies, active tappers, and the desired heuristic
            int asynchAdjust = met.scheduleNext(
                currAsynch,
                tapperIsConnected,
                GEM_MAX_TAPPERS,
                GEM_METRONOME_HEURISTIC_AVERAGE
            );

            // when does this window end
            windowEnds = met.next + (met.getIOI()/2);


            // Send data to the ECC
            /*NOTE: each data packet sent to ECC conists of 12 bytes
                -4 for the metronome tone onset (Long on Uno is 4 bytes)
                -8 for the 4 asynchronies (ints on Uno are 2 bytes)
            It's up to the ECC to correctly parse the byte stream.
            NOTE that this is version 0.0.0 and only incudes raw data (no
            meta-info) to keep the stream as light as possible, future versions
            will include more met-data if performance testing results suggest
            that that is feasible within our time constraints
            -SA 20170628
            */
            
            // Only send data if this isn't the first window
            if (window > 0){
                //first byte is the data transfer protocol identifier
                Serial.write(GEM_DTP_RAW);

                // Send current window to ECC - 20170703 LF
                Serial.write((byte *)window, sizeof (uint16_t));

                /*NOTE: next, send the scheduled time of the metronome tone for
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

                /*NOTE: this is a good example of how a ScopedVolatileLock should be
                used. the extra {} creates a new scope so <lock> is released
                immediatly after Serial.write() is finished (i.e. the {} are
                *CRITICAL*) -SA 20170702
                WARNING: the gotcha here is that the actual data transmission
                relies on an ISR, so this means that no data will be transmitted
                until after the write is finished (i.e. Serial.write() just moves
                the data into a buffer which triggers an ISR to perform the send)
                the alternate method would be to do the loop ourselves and only
                disable interrupts while we read a value from <currAsynch>
                -SA 20170702
                */
                {
                    ScopedVolatileLock lock;
                    Serial.write((byte *)currAsynch, sizeof (int) * GEM_MAX_TAPPERS);

                    // Send calculated metronome adjustment to ECC
                    Serial.write((byte *)&asynchAdjust, sizeof (int));

                    // reset the current tap times
                    for (uint8_t s = 0; s < GEM_MAX_TAPPERS; ++s)
                    {
                        currAsynch[s] = NO_RESPONSE;
                    }
                }
            }

            #ifdef DEBUG
                Serial.print(F("Now: "));
                Serial.println(currentTime);

                Serial.print(F("Schd "));
                Serial.print(window);
                Serial.print(F(": "));
                Serial.println(met.next);
            #endif

            // Increment our window counter
            window++;

        } // if (currentTime >= windowEnds)

        // Check whether we have passed the scheduled metronome time
        if ((currentTime >= met.next) && !met.played)
        {
            #ifdef DEBUG
                Serial.println(F("SND"));
            #endif
            sound.play(); // play the sound

            met.played = true; // flag that it has been played

            #ifdef DEBUG
                Serial.println(F("USND"));
            #endif
        }
    } //if (TRIAL_RUNNING)

}

/////////////////////////////////////////////////////////
//////////////// ARDUINO Loop() FUNCTION ////////////////
/////////////////////////////////////////////////////////

void loop()
{
    //NOTE: each state function (run() and idle()) are responsible for correctly
    //indicating transitions (as signaled by the ECC) by setting the global
    //GEM_CURRENT_STATE -SA 20170706
    switch (GEM_CURRENT_STATE)
    {
        case GEM_STATE_RUN:
            run();
            break;
        case GEM_STATE_IDLE:
            idle();
            break;
    }

}

/////////////////////////////////////////////////////////////////////
////////////////////////////    Loop() End ////////////////////////////
/////////////////////////////////////////////////////////////////////
