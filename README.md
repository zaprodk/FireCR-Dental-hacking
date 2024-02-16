# FireCR-Dental-hacking
 Hacking the DigiRay/3DISC FireCR scanner for fun

The device is run by a STM32F427IIT6-CPU with a color LCD touchscreen.

The scanning of the PSP Imaging plate is done by a Altera EP4CE15E22C8N Cyclone IV-FPGA

The main graphical resources is held on MicroSD-card and scans are also saved to SD-card, as well as streamed over Ethernet to the controlling application.

The main application comes with a DentalCR_SystemUpdater_1.1.2.exe that can update the target STM32/FPGA/Graphics etc. The unpacked data from the .exe is found in this repository.

