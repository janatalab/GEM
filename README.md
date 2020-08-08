# GEM
This is a repository for code associated with the NAKFI Groove Enhancement Machine (GEM) project led by Petr Janata at UC Davis.

The GEM consists of a set of Arduinos that communicate with each other and with a computer (a MacBook Pro is being used for development) running experiment control software written in Python.

There is one "master" Arduino that functions as the adaptive metronome and which communicates with the computer.  The other Arduinos, one for each participant, are connected to force-sensitive resistors (FSRs) and also to the Master Arduino.

# Directories
## GEM 
Contains the C++ files that make up the GEM library.

## GUI 
Contains the python files that comprise the graphical user interface, run on the experiment control computer.

## Master_Adaptive
Contains the sketch that is downloaded to the Master Arduino.

## Slave_Adaptive
Contains the sketch that is downloaded to the Slave Arduino.

# Instructions
By default, the Arduino software expects to see directories in the Arduino directory, and libraries within a directory called "libraries". The simplest thing to do is to clone the repository within the Arduino directory and then make a symbolic link to the GEM library directory from within the libraries directory.

# Dependencies
This project depends on the following libraries:
<ul>
<li>WaveHC
<li>EnableInterrupt
</ul>

# Contributions
Initial versions of the code were developed by Wisam Reid (at CCRMA at Stanford) and David Miranda (Case Western Reserve University), with input from Lauren Fink (UC Davis) and Petr Janata (UC Davis).  Wisam, David, and Lauren constructed and started debugging the initial setup in August 2016.  The code was refactored by Petr Janata in March 2017, and constitutes the starting point for this repository. The end of June and beginning of July 2017 saw a huge push by Lauren Fink and Scottie Alexander to clean-up, make the code much more robust, and implement the first version of the GUI.


# Citation
Paper associated with this code:
Fink, Alexander, & Janata (submitted). A multi-person adaptive metronome enhances synchrony amongst groups of tappers. TODO PsyArXiv

DOI for this code repository:
TODO
