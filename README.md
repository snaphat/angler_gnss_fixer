# angler_gnss_fixer

## About
A [Magisk](https://magiskmanager.com) module that fixes GNSS/GPS on the Nexus 6p running the Android 10 Pixel Experience rom.
  
## Installation
  * Install the gnss_fixer.zip via Magisk Manager.
  
## Clone:
```
git clone git@github.com:snaphat/angler_gnss_fixer.git
```

## Technical Explanation
The current build of the Pixel Experience 10 rom contains a bug that caused the GNSS (GPS) service to repeatedly crash when the GPS is put into use. This makes it unable to lock any satellite. The log of this error is shown below: 
```
10-10 02:25:49.449  6425  6425 F DEBUG   : Build fingerprint: 'google/angler/angler:8.1.0/OPM3.171019.014/4503998:user/release-keys'
10-10 02:25:49.451  6425  6425 F DEBUG   : Revision: '0'
10-10 02:25:49.451  6425  6425 F DEBUG   : ABI: 'arm64'
10-10 02:25:49.453  6425  6425 F DEBUG   : Timestamp: 2019-10-10 02:25:49-0400
10-10 02:25:49.453  6425  6425 F DEBUG   : pid: 6320, tid: 6338, name: Loc_hal_worker  >>> /vendor/bin/hw/android.hardware.gnss@1.0-service <<<
10-10 02:25:49.453  6425  6425 F DEBUG   : uid: 1021
10-10 02:25:49.453  6425  6425 F DEBUG   : signal 6 (SIGABRT), code -1 (SI_QUEUE), fault addr --------
10-10 02:25:49.453  6425  6425 F DEBUG   : Abort message: 'Check failed: data[size] == '\0' '
10-10 02:25:49.453  6425  6425 F DEBUG   :     x0  0000000000000000  x1  00000000000018c2  x2  0000000000000006  x3  000000782277f850
10-10 02:25:49.453  6425  6425 F DEBUG   :     x4  0000000000000000  x5  0000000000000000  x6  0000000000000000  x7  7f7f7f7f7f7f7f7f
10-10 02:25:49.453  6425  6425 F DEBUG   :     x8  00000000000000f0  x9  0000007823e294e0  x10 0000000000000000  x11 0000000000000001
10-10 02:25:49.453  6425  6425 F DEBUG   :     x12 000000782386220c  x13 ffffffffffffffff  x14 0000000000000004  x15 ffffffffffffffff
10-10 02:25:49.453  6425  6425 F DEBUG   :     x16 0000007823ef78c0  x17 0000007823ed50f0  x18 0000007822b65000  x19 00000000000000ac
10-10 02:25:49.453  6425  6425 F DEBUG   :     x20 00000000000018b0  x21 00000000000000b2  x22 00000000000018c2  x23 00000000ffffffff
10-10 02:25:49.453  6425  6425 F DEBUG   :     x24 0000007822780020  x25 0000000000063e69  x26 0000000000000005  x27 000000782277fb40
10-10 02:25:49.453  6425  6425 F DEBUG   :     x28 00000078231a7010  x29 000000782277f900
10-10 02:25:49.453  6425  6425 F DEBUG   :     sp  000000782277f830  lr  0000007823e880f0  pc  0000007823e88120
10-10 02:25:49.465  6425  6425 F DEBUG   :
10-10 02:25:49.465  6425  6425 F DEBUG   : backtrace:
10-10 02:25:49.466  6425  6425 F DEBUG   :       #00 pc 0000000000083120  /apex/com.android.runtime/lib64/bionic/libc.so (abort+176) (BuildId: 56d83705c77e9d221c7ec590a8636f73)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #01 pc 000000000000bc3c  /system/lib64/libbase.so (android::base::DefaultAborter(char const*)+12) (BuildId: 729b9093d9cf9052d8b28c8f6d431cc6)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #02 pc 000000000000c650  /system/lib64/libbase.so (android::base::LogMessage::~LogMessage()+608) (BuildId: 729b9093d9cf9052d8b28c8f6d431cc6)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #03 pc 000000000005211c  /system/lib64/libhidlbase.so (android::hardware::hidl_string::setToExternal(char const*, unsigned long)+348) (BuildId: f7c91e8abfdcb31460e070ef2996507a)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #04 pc 0000000000011994  /vendor/lib64/hw/android.hardware.gnss@1.0-impl.so (android::hardware::gnss::V1_0::implementation::Gnss::nmeaCb(long, char const*, int)+84) (BuildId: a708836eec9febdef9fbe8a162e09096)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #05 pc 00000000000178f4  /system/lib64/libloc_eng.so (loc_eng_nmea_send(char*, int, loc_eng_data_s*)+292) (BuildId: d3f84f2979abcaaa4aca109c1cc50914)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #06 pc 0000000000018b60  /system/lib64/libloc_eng.so (loc_eng_nmea_generate_sv(loc_eng_data_s*, GpsSvStatus const&, GpsLocationExtended const&)+800) (BuildId: d3f84f2979abcaaa4aca109c1cc50914)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #07 pc 0000000000006118  /system/lib64/libloc_core.so (loc_core::MsgTask::loopMain(void*)+128) (BuildId: 589826f4b884e7cd4d5e5bac88716d5e)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #08 pc 000000000001002c  /vendor/lib64/hw/android.hardware.gnss@1.0-impl.so (threadFunc(void*)+12) (BuildId: a708836eec9febdef9fbe8a162e09096)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #09 pc 00000000000e43f4  /apex/com.android.runtime/lib64/bionic/libc.so (__pthread_start(void*)+36) (BuildId: 56d83705c77e9d221c7ec590a8636f73)
10-10 02:25:49.466  6425  6425 F DEBUG   :       #10 pc 0000000000084d18  /apex/com.android.runtime/lib64/bionic/libc.so (__start_thread+64) (BuildId: 56d83705c77e9d221c7ec590a8636f73)
```

### Details

More specifically, it appears an [off by one error in loc_eng_nmea_put_checksum()](https://android.googlesource.com/platform/hardware/qcom/gps/+/refs/heads/android10-release/msm8994/loc_api/libloc_api_50001/loc_eng_nmea.cpp#69) causes a check in [/system/lib64/libhidlbase.so:SetToExternal()](https://android.googlesource.com/platform/system/libhidl/+/refs/heads/android10-release/base/HidlSupport.cpp#260) to fail.

Note, I'm not 100% sure where this code is located in the Pixel Experience 10 rom (I don't know where the src is hosted), but the dissassambled libraries contain the problem. I was unable to find a good way to directly patch libloc_eng.so (without changing the binary size, etc.) so instead I removed the error check in libhidlbase.so and then corrected the size directly there. Note the best spot, but it seems to do the trick.

The following [commit](https://github.com/z3c-pie/device_sony_msm8974-common/commit/12543c3693e3d55602e3cacbec1f80b44bb80854#diff-62d39461a97da6ab4ced4ef122957333) in some other android repository shows a source fix for the problem, but the newer qcomm code in the Android 10 repository doesn't contain the fix for some reason.

Also, notably, the reason Android 9 doesn't fail for the Nexus 6p is simply because the offending check doesn't exist in the older code base: [Android 9 msm8894 loc_eng_nmea.cpp](https://android.googlesource.com/platform/system/libhidl/+/refs/tags/android-9.0.0_r49/base/HidlSupport.cpp#255).

### Images
#### Original Basic Block
Below is the original code shown in [Ghidra](https://ghidra-sre.org/). The check is done on line 15 and the code from line 20-25 cause an abort. Note, Ghidra's reversed source code is a little weird.
![Original Basic Block](https://github.com/snaphat/angler_gnss_fixer/blob/assets/orig.png)

#### Modified Basic Block
Below is the modified code. The offending else condition logic is removed and instead replaced with an addition to the length and a bunch of no-op operations. Note the actual machine code shown on the left. Simple 4 byte instructions.
![Modified Basic Block](https://github.com/snaphat/angler_gnss_fixer/blob/assets/mod.png)
