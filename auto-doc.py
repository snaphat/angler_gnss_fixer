import sys, os

#Append to the path.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from autodoc import *

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
'''--------------------------------------------------------------------------'''
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# enableService: specifies to run auto-doc as a service on system startup
# enableSilence: specifies auto-doc to be silent when running
# enableSimulation: run a simulation without modifying any files on disk
autodoc.setup(enableService=False, enableSilence=False, enableSimulation=False);

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
'''--------------------------------------------------------------------------'''
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

list = ["libloc_eng.so"];
for item in list:
#{
    #The binary to modify
    hack = binary(item);

    if (hack.prologue()):
    #{
         # (Fix for buffer overrun crash at copying nmea string, see: https://github.com/z3c-pie/device_sony_msm8974-common/commit/6991f2087d166e0c89e4c2f4c34eb28d82d1bd74)
        # Modify LocEngReportNmea constructor to copy A NULL terminator after the nmea string without affecting the actual size:
        tuple     = [
                        "\x76\\\x7e\x40\x93\xF5",
                        0,
                        "\x76\x06\0\x11",
                    ];
        hack.modify(tuple, allowedDuplicateCount=1, ignoredDuplicates=None, memset=None, offsetRange=None);
        # Switch memcpy to strlcpy
        tuple     = [
                        "\x30\x31\0\x94",
                        0,
                        "\x70",
                    ];
        hack.modify(tuple, allowedDuplicateCount=1, ignoredDuplicates=None, memset=None, offsetRange=None);

        # (gps: Return the correct length of nmea sentence, see: https://github.com/z3c-pie/device_sony_msm8974-common/commit/74894e7a402906920a5a92e50bd61db0984bec04)
        # Note: loc_eng_nmea_put_checksum is inlined and never called directly or externally.
        #       Moreover, loc_eng_nmea_send is always paired with each inline call to loc_eng_nmea_put_checksum
        #       So the length correction is done there for ease.

        #       so the fix is done in loc_eng_nmea_send because
        tuple     = [
                        "\xF4\x03\x01\\\x2a....\xF3",
                        0,
                        "\x34\x04\0\x11",
                    ];
        hack.modify(tuple, allowedDuplicateCount=1, ignoredDuplicates=None, memset=None, offsetRange=None);

        # error checks for binary modification done here.
        hack.epilogue();
    #}
#}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
'''--------------------------------------------------------------------------'''
'''~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'''
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# More error checks done here. For example, if multiple binaries were patched
# And some post-binary modification process failed.
autodoc.teardown();
