# GEM
This is Lauren Fink's version of the GEM library and GUI that is still under heavy development. Anticated finish date: July 2nd, 2017. 
Scottie Alexander (a fellow neuroscience graduate student, former programmer) helped Lauren in developing the structure and functionality of this code.  

Current State: 
- The GUI visual is complete but messages to Arduino still need to be sent to Master using PySerial. This is my goal for the week. 
- GEM code has been completely restructured and still requires a fair amount of debugging. The structure for sending messages to ECC is already in place in GEMMasterArduino.h. A few more modules and functions remain to be added. 

NB: Some of Petr's old GEM code is still mixed in with this repository but no longer relevant (it is still in here because I am using it for reference). 

# Directories and Files
## GEM 
Contains the C++ files that make up the GEM library.  
GEMArduino.h, GEMMasterArduino.h, GEMSlaveArduino.h are core files - all still under development.

## GEM GUI
- GEMGUI.py contains all of the code that builds the GUI
- gem_example.py contains example presets and code to run the GUI

## GEMError
Class for reporting errors. GEMErrorCodes.h contains error code constants. 
Still under development.

## GEMSound 
Has been restructured in GEMSound.h. Old verions called GEMsound_orig

## Master_Adaptive
TODO: will update this once running version ready

## Slave_Adaptive 
TODO: will update this once running version ready

# Dependencies
This project depends on in number of other libraries:
<ul>
<li>WaveHC
<li>EnableInterrupt
</ul>

# Contributions
Initial versions of the code were developed by Wisam Reid (at CCRMA at Stanford), Lauren Fink (UC Davis) and David Miranda (Case Western Reserve University), with input from Petr Janata (UC Davis).  Wisam, David, and Lauren constructed and started debugging the initial setup in August 2016.  The code was refactored by Petr Janata in March 2017. The code was then refactored again by Lauren Fink and Scottie Alexander in June 2017. 
