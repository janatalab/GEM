#include "GEMConstants.h"

// #define write_time() (Serial.write((byte *)millis(), sizeof (unsigned long)))

uint8_t run = 0;
uint8_t glen = 255;
uint8_t garray[255];

void write_time()
{
    unsigned long now = millis();
    Serial.write((byte *)&now, sizeof (unsigned long));
}

void setup()
{
    Serial.begin(115200);

    for (uint8_t k = 0; k < glen; ++k)
    {
        garray[k] = 255 - k;
    }
}

void write_packet_array(uint8_t *ary, uint8_t n)
{
    Serial.write(n);

    write_time();

    Serial.write(ary, n);

    write_time();
}

void write_packet()
{
    uint8_t nbyte = 255;

    Serial.write(nbyte);

    write_time();

    for (uint8_t k = 0; k < nbyte; ++k)
    {
        Serial.write(k);
    }

    write_time();
}

void loop()
{
    if (Serial.available())
    {
        run = (uint8_t)Serial.read();
    }

    if (run == GEM_START) { write_packet_array(garray, glen); }
    delay(1);
}
