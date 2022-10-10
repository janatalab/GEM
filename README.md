# GEM (Groove Enhancement Machine)

![gem](https://github.com/janatalab/GEM/blob/main/Images/GEMlogo.svg "The GEM banner")

# About
This is a repository for code associated with the NAKFI Groove Enhancement Machine (GEM) project led by Petr Janata at UC Davis.

The GEM consists of a set of Arduinos that communicate with each other and with a computer running experiment control software written in Python.

The "Metronome" Arduino functions as the adaptive metronome and communicates with the computer. A force-sensitive resistor (FSR) is connected to each of the other Arduinos, the "Tapper" Arduinos, utilizing a scheme first described by Schulz & van Vugt (2016). The Tapper Arduinos communicate tap events via interrupts to the Metronome Arduino which adjusts the time of the next metronome tone based on the individual tap times and parameters that have been communicated from the experiment control computer (ECC).

[Further instructions and project information can be found in the Wiki](https://github.com/janatalab/GEM/wiki).

## Overview

- [Directories](#Directories)
- [Dependencies](#Dependencies)
- [Installation instructions](#Instructions)
- [Citations](#Citations)


# Directories
### GEM 
Contains the C++ files that make up the GEM library.

### GUI 
Contains the python files that comprise the graphical user interface, run on the experiment control computer.

### Master_Adaptive
Contains the sketch that is downloaded to the Master Arduino.

### Slave_Adaptive
Contains the sketch that is downloaded to the Slave Arduino.

# Dependencies
Although the project was originally developed to run on Python 2, it has been ported to Python 3. The first release version has been tested using:
- macOS 12.2.1 (Monterey)
- Python 3.10.0
- Arduino IDE 1.8.19

This project depends on the following third-party libraries which you should install in your system's Arduino/libraries folder following the instructions at [http://www.arduino.cc/en/Guide/Libraries](http://www.arduino.cc/en/Guide/Libraries):

- WaveHC (<=1.0.2)
- EnableInterrupt (originally developed using EnableInterrupt library version 0.9.5, but this appears not to be working properly in the newer version)

# Instructions
Detailed installation instructions are available in the [wiki](https://github.com/janatalab/GEM/wiki/Installation). 

By default, the Arduino software expects to see project directories in the Arduino directory, e.g. /Users/janatalab/Documents/Arduino. The path can be set under the Arduino->Preferences...

Arduino libraries are located within a directory called "libraries", as are any libraries that are installed in support of a project, such as the third-party libraries listed above.

We recommend either cloning the repository within the Arduino directory or creating a symbolic link (symlink) to the git repository location.

Within the Arduino libaries directory, make a symbolic link to this repository's GEM directory which contains the GEM library.

After launching a Python virtual environment, e.g. virtualenv, that you have created for this project, install the required Python files using the requirements.txt file in the GUI directory.

See the Wiki for further setup instructions.

# Citations
Schultz, B. G., & van Vugt, F. T. (2016). Tap Arduino: An Arduino microcontroller for low-latency auditory feedback in sensorimotor synchronization experiments. Behavior Research Methods, 48(4), 1591–1607. [https://doi.org/10.3758/s13428-015-0671-3](https://doi.org/10.3758/s13428-015-0671-3)

The GEM was originally described and published in the following paper:

Fink, L.K., Alexander, P.C., & Janata, P. (2022). The Groove Enhancement Machine (GEM): A multi-person adaptive metronome to manipulate sensorimotor synchronization and subjective enjoyment. *Front. Hum. Neurosci. 16*:916551. [doi: 10.3389/fnhum.2022.916551](https://doi.org/10.3389/fnhum.2022.916551)

Please cite the paper if using anything from this repository. 

Note that more information about the proof-of-concept experiments reported in the paper is available in a separate git repository: [https://github.com/janatalab/GEM-Experiments-POC](https://github.com/janatalab/GEM-Experiments-POC)


