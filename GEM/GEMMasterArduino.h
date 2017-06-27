#ifndef GEMMASTERARDUINO_H_
#define GEMMASTERARDUINO_H_

#define EI_ARDUINO_INTERRUPTED_PIN
#include "EnableInterrupt.h"
#include "GEMConstants.h"
#include "GEMArduino.h"
#include "Arduino.h"

/* =============================================================================
TODO:
    1) Within the GEM master sketch loop function, we need to check to see if
    any GEMSlaveIO objects got a tap, and if so send forward it to the ECC
        * loop over GEMSlaveIO objs, collect all tap times, send all to ECC thus
        minimizing the number of packets we have to send to ECC
============================================================================= */

/* ========================================================================== */
class GEMSlaveIO
{
public:
    volatile bool isConnected;
    volatile unsigned long lastTapTime;
    uint8_t pin;
    uint8_t index;
    /* ---------------------------------------------------------------------- */
    GEMSlaveIO() : pin(0), index(0), isConnected(false), lastTapTime(0) {};
    /* ---------------------------------------------------------------------- */
    ~GEMSlaveIO() {};
    /* ---------------------------------------------------------------------- */
    inline void I2CBegin() const { Wire.beginTransmission(index + 1); }
    inline void I2CEnd() const { Wire.endTransmission(); }
    /* ---------------------------------------------------------------------- */
    void I2CWrite(uint8_t val) const
    {
        if (isConnected)
        {
            I2CBegin();
            Wire.write(val);
            I2CEnd();
        }
    }
    /* ---------------------------------------------------------------------- */
    void clearInterrupt()
    {
        disableInterrupt(pin);
    }
    /* ---------------------------------------------------------------------- */
    void initHandshake(void) const
    {
        //NOTE: can you pass a non-static memeber function as a interrupt callback?
        enableInterrupt(pin, processHandshake, RISING);
    }
    /* ---------------------------------------------------------------------- */
    void processHandshake(void)
    {
        isConnected = true;
    }
    /* ---------------------------------------------------------------------- */
    void initTap(void) const
    {
        clearInterrupt();
        delay(1);
        //NOTE: can you pass a non-static memeber function as a interrupt callback?
        enableInterrupt(pin, processTap, RISING);
    }
    /* ---------------------------------------------------------------------- */
    void processTap(void)
    {
        cli(); //disable interrupts
        lastTapTime = micros();
        sei(); //enable interrupt
    }
    /* ---------------------------------------------------------------------- */
    void sendParameter(uint8_t pid, const String &msg)
    {
        if (isConnected)
        {
            //combine the parameter id (pid) and string into a single buffer
            //and terminate with '\n'
            int len = msg.length();
            char buf[len + 2];
            buf[0] = (char)pid;
            memcpy(buf+1, msg.c_str(), len);
            buf[len] = '\n';

            I2CBegin();
            Wire.write(buf, len+2);
            I2CEnd();
        }
    }
    /* ---------------------------------------------------------------------- */

};
/* ========================================================================== */
class GEMMasterArduino : public GEMArduino
{
    GEMMasterArduino(uint8_t id, GEMError *err) :
        GEMArduino(uint8_t id, GEMError *err),
        _nSlavesReq(0)
    {};
    /* ---------------------------------------------------------------------- */
    ~GEMMasterArduino() : {};
    /* ---------------------------------------------------------------------- */
    void initialize() override
    {
        // join I2C communication as master (i.e. no address specified)
        Wire.begin();

        //establish communication link with ECC and get parameters from it
        Serial.begin(GEM_SERIAL_BAUDRATE, SERIAL_8N1);

        //wait until serial port connects
        while (!Serial)
        {
            delay(10);
        }

        uint8_t nInit = initializeSlaves();

        while (!isInitialized())
        {
            //wait for ECC to begin sending messages
            while (Serial.available() <= 0)
            {
                delay(10);
            }

            processMsg();

            flushSerialBuffer();
        }

        if (nInit != _nSlavesReq)
        {
            //error?
        }

        //TODO
        //check if each slave is ready (i.e. wav file is loaded etc.)
    }
    /* ---------------------------------------------------------------------- */
    bool isInitialized() const override
    {
        return _snd.isInitialized() & _met.isInitialized();
    }
    /* ---------------------------------------------------------------------- */
    void processMsg()
    {
        uint8_t buf[2]; // 0 = address; 1 = parameter ID, 2 = value
        Serial.readBytes(buf, 2);

        switch (buf[0])
        {
            case GEM_STOP_EXP:
                break;
            case GEM_START_EXP:
                //is our master GEMSound ready to roll?
                //is the metronome ready to roll?
                //are the slaves ready to roll?
                break;
            case GEM_QUERY_STATE:
                //reply to the ECC what our state
                break;
            case GEM_MASTER_ID:
                setParameter(buf[1]);
                break;
            case GEM_SLAVE1_ID:
            case GEM_SLAVE2_ID:
            case GEM_SLAVE3_ID:
            case GEM_SLAVE4_ID:
                _slaves[buf[0] - GEM_SLAVE1_ID].sendParameter(buf[1],
                    Serial.readStringUntil('\n'));
                break;
            default:
                //error?
        }
    }
    /* ---------------------------------------------------------------------- */
    void setParameter(uint8_t pid)
    {
        switch (pid)
        {
            case GEM_METRONOME_ALPHA:
                _met.setAlpha(Serial.parseFloat());
                break;
            case GEM_METRONOME_TEMPO:
                _met.setTempo(Serial.parseInt());
                break;
            case GEM_WAV_FILE:
                _snd.setWaveID(static_cast<uint8_t>(Serial.parseInt()));
                break;
            case GEM_NUM_SLAVES_REQ:
                _nSlavesReq = Serial.parseInt();
                break;
            default:
                //error?
        }
    }
    /* ---------------------------------------------------------------------- */
    uint8_t initializeSlaves()
    {
        const uint8_t slavePins[] = {6, 7, 8, 9};

        uint8_t nslaves = 0;

        //iterate through slaves, set up and execute handshake, set up to recieve taps
        for (uint8_t k = 0; k < GEM_MAX_SLAVES; ++k)
        {
            _slaves[k].pin = slavePins[k];
            _slaves[k].index = k;

            //enable interrupt for processing handshakes
            _slaves[k].initHandshake();

            //tell the slave that we are ready for them to toggle the interrupt
            //pin
            _slaves[k].I2CWrite(GEM_REQUEST_ACK);

            //pause to allow the slave to reply
            delay(GEM_HANDSHAKE_TIMEOUT);

            if (_slaves[k].isConnected)
            {
                _slaves[k].initTap();
                ++nslaves;
            }
        }
        return nslaves;
    }
    /* ---------------------------------------------------------------------- */
    void sendTimestampToECC(uint8_t id, unsigned long t)
    {
        Serial.write(id);

        //Serial.write only writes single bytes at a time, so to send an
        //unsigned long (such as that returned by millis or micros) we need to
        //send each of the *4* bytes individually, so we start with the low byte
        //and proceed to the high byte
        Serial.write(t & 0xff);
        Serial.write((t >> 8) & 0xff);
        Serial.write((t >> 16) & 0xff);
        Serial.write((t >> 24) & 0xff);
    }
    /* ---------------------------------------------------------------------- */
private:
    /* ---------------------------------------------------------------------- */
    void flushSerialBuffer()
    {
        while (Serial.available() > 0)
        {
            char t = Serial.read();
        }
    }
    /* ---------------------------------------------------------------------- */
private:
    GEMSlaveIO[GEM_MAX_SLAVES] _slaves;
    GEMMetronome _met;
    uint8_t _nSlavesReq;
};
/* ========================================================================== */
#endif
