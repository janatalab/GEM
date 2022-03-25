# GEM (Groove Enhancement Machine)

[gem](GEMlogo.svg "The GEM banner")

This is a repository for code associated with the NAKFI Groove Enhancement Machine (GEM) project led by Petr Janata at UC Davis.

The GEM consists of a set of Arduinos that communicate with each other and with a computer running experiment control software written in Python.

The "Metronome" Arduino functions as the adaptive metronome and which communicates with the computer. A force-sensitive resistor (FSR) is connected to each of the other Arduinos, the "Tapper" Arduinos, utilizing a scheme first described by Schulz & van Vugt (2016). The Tapper Arduinos communicate tap events via interrupts to the Metronome Arduino which adjusts the time of the next metronome tone based on the individual tap times and parameters that have been communicated from the experiment control computer (ECC).

[Further instructions and project information can be found in the Wiki](https://github.com/janatalab/GEM/wiki).

# Directories
## GEM 
Contains the C++ files that make up the GEM library.

## GUI 
Contains the python files that comprise the graphical user interface, run on the experiment control computer.

## Master_Adaptive
Contains the sketch that is downloaded to the Master Arduino.

## Slave_Adaptive
Contains the sketch that is downloaded to the Slave Arduino.

# Dependencies
Although the project was originally developed to run on Python 2, it has been ported to Python 3. The first release version has been tested using:
- macOS 12.2.1 (Monterey)
- Python 3.10.0
- Arduino IDE 1.8.19

This project depends on the following third-party libraries which you should install in your system's Arduino/libraries folder following the instructions at [http://www.arduino.cc/en/Guide/Libraries](http://www.arduino.cc/en/Guide/Libraries):

- WaveHC
- EnableInterrupt (originally developed using EnableInterrupt library version 0.9.5, but this appears not to be working properly in the newer version)

# Instructions
By default, the Arduino software expects to see project directories in the Arduino directory, e.g. /Users/janatalab/Documents/Arduino. The path can be set under the Arduino->Preferences...

Arduino libraries are located within a directory called "libraries", as are any libraries that are installed in support of a project, such as the third-party libraries listed above.

We recommend either cloning the repository within the Arduino directory or creating a symbolic link (symlink) to the git repository location.

Within the Arduino libaries directory, make a symbolic link to this repository's GEM directory which contains the GEM library.

After launching a Python virtual environment, e.g. virtualenv, that you have created for this project, install the required Python files using the requirements.txt file in the GUI directory.

See the Wiki for further setup instructions.

# Citations
Schultz, B. G., & van Vugt, F. T. (2016). Tap Arduino: An Arduino microcontroller for low-latency auditory feedback in sensorimotor synchronization experiments. Behavior Research Methods, 48(4), 1591–1607. [https://doi.org/10.3758/s13428-015-0671-3](https://doi.org/10.3758/s13428-015-0671-3)

Paper associated with this code:
Fink, Alexander, & Janata (submitted). A multi-person adaptive metronome enhances synchrony amongst groups of tappers. 

DOI for this code repository:
TODO
