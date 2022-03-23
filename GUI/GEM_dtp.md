# GEM data transfer protocols

## Metronome -> ECC
    * 0: data transfer protocol id
    * 1-2: window number (uint16)
    * 3-6: scheduled time of the metronome click (uint32)
    * 7-14: subject asynchronies (4 - int16s) constant order
    * 15-16: metronome time adjustment value for the next window (ms) (int16)

## Data file format
