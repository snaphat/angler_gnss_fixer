import distutils.dir_util #for multiple file copy.
import getpass            #for username.
import glob               #for globbing paths.
import os                 #fs stat and path check.
import re                 #regex.
import shutil             #move and copy files.
import string             #for string replacal.
import StringIO           #for redirecting stdout and stderr.
import subprocess         #run a subprocess.
import sys                #various system functions.
import tempfile           #for temporary directories.
import time               #for time.

#Set the path to the current directory.
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])));

#Enable color support if available.
try:
#{
    import colorama;
    colorama.init();

    #Setup color shortcuts.
    BLACK =   colorama.Style.BRIGHT + colorama.Fore.BLACK;
    RED =     colorama.Style.BRIGHT + colorama.Fore.RED;
    GREEN =   colorama.Style.BRIGHT + colorama.Fore.GREEN;
    YELLOW =  colorama.Style.BRIGHT + colorama.Fore.YELLOW;
    BLUE =    colorama.Style.BRIGHT + colorama.Fore.BLUE;
    MAGENTA = colorama.Style.BRIGHT + colorama.Fore.MAGENTA;
    CYAN =    colorama.Style.BRIGHT + colorama.Fore.CYAN;
    WHITE =   colorama.Style.BRIGHT + colorama.Fore.WHITE;
    RESET =   colorama.Style.RESET_ALL;
#}
except:
#{
    #Fallback to non-colored mode.
    BLACK     = '';
    RED       = '';
    GREEN     = '';
    YELLOW    = '';
    BLUE      = '';
    MAGENTA   = '';
    CYAN      = '';
    WHITE     = '';
    RESET     = '';
#}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~~~~~~ Returns the temporary directory with the specified file appended. ~~~~~
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def tempdir(filename=None):
#{
    local = lambda:0;
    #No temp directory set.
    if (not hasattr(tempdir, "location")):
    #{
        #Try to set one.
        try:
        #{
            tempdir.location = tempfile.mkdtemp(dir=os.getcwd());
        #}
        except:
        #{
            #Failed - return nothing.
            return None;
        #}
    #}

    #check if a filename was provided.
    if (filename == None):
    #{
        #Return just the temporary directory.
        return tempdir.location;
    #}
    else:
    #{
        #Append filename.
        return os.path.join(tempdir.location, filename);
    #}
#}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~~~~~~~~~~~~ Class to handle general patching related activities. ~~~~~~~~~~~~
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class autodoc:
#{
    enableService = False;    #Whether to ask to install as a service.
    enableSilence = False;    #Whether we are to execute silently or not.
    enableSimulation = False; #Whether we are testing the hack.
    reversing = False;        #Whether to reverse backups.
    found = False;            #If any binaries are found.
    error = False;            #If any modifications had errors.
    backupList = [];          #List of backed up binaries.
    helpInfo = [];            #List of user help arguments.
    arguments = [];           #List of user arguments and their functions.
    preSetupCode = [];        #List of functions to be run on pre-setup.
    postSetupCode = [];       #List of functions to be run on post-setup.
    preTeardownCode = [];     #List of functions to be run on pre-teardown.
    postTeardownCode = [];    #List of functions to be run on post-teardown.

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~ Overridden Exception Handler with Color and More. ~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def exception_handler(type, value, traceback):
    #{
        #Reverse any backups we did before crashing.
        autodoc.reverse_backups();

        #Swap standard error to a string.
        orig_stderr = sys.stderr;
        sys.stderr = str_stderr = StringIO.StringIO();

        #Call the original exception handler.
        sys.__excepthook__(type, value, traceback);

        #Swap standard error back.
        sys.stderr = orig_stderr;

        #Grab the trace.
        trace = str_stderr.getvalue();

        #Color numbers.
        regex   = re.compile("line [0-9]+,");
        for match in regex.finditer(trace):
            replacal = match.group(0).rstrip(",");
            trace = trace.replace(replacal, YELLOW + replacal + RESET);

        #Color filenames.
        regex   = re.compile("File \\\".+\\\"");
        for match in regex.finditer(trace):
            replacal = match.group(0).lstrip("File \"").rstrip("\"");
            trace = trace.replace(replacal, CYAN + replacal + RESET);

        #Color modules.
        regex   = re.compile(", in.+\\\n");
        for match in regex.finditer(trace):
            replacal = match.group(0).lstrip(", in ");
            trace = trace.replace(replacal, GREEN + replacal + RESET);

        #Color code.
        regex   = re.compile("    .+");
        for match in regex.finditer(trace):
            replacal = match.group(0);
            trace = trace.replace(replacal, RED + match.group(0) + RESET);

        #Print colored trace.
        print "\nUnhandled exception:"
        print trace;

        #Call our exit method.
        autodoc.exit();
    #}
    sys.excepthook = autodoc = exception_handler;

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~ Tries to re-execute as admin upon error. ~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def escalate_admin():
    #{
        #On non-windows platforms try to execute as root.
        if os.name != "nt" and os.geteuid() != 0:
        #{
            display.info("Please re-execute with administrator privileges by providing your password below...");
            display.info("Please note, no characters will be shown when typing...");
            # os.execvp() replaces the running process, rather than launching a child
            # process, so there's no need to exit afterwards. The extra "sudo" in the
            # second parameter is required because Python doesn't automatically set $0
            # in the new process.
            os.execvp("sudo", ["sudo"] + sys.argv);
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~ Locates the specified binaries by searching. ~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def find_binaries(directories, list):
    #{
        expandedSet = set();
        for directory in directories:                       #Iterate over specified directories.
            for path, subdirs, files in os.walk(directory): #Walk recursively through each directory.
                for file in files:                          #Iterate over files in the directory.
                    for binary in list:                     #Iterate over binaries.
                        if (file == binary):                #Check if binary found.
                            expandedSet.add(os.path.join(path, binary));

        #return valid binary list.
        return sorted(expandedSet);
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~ Locates the specified binaries by globbing. ~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def glob_binaries(list):
    #{
        expandedSet = set();
        for item in list:
        #{
            #expand entry -- empty if it doesn't match any valid binaries.
            expandedItem = glob.glob(item);

            #Iterate over matches and add them to our list of valid binaries.
            for entry in expandedItem:
            #{
                expandedSet.add(entry);
            #}
        #}

        #return valid binary list.
        return sorted(expandedSet);
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~ Locates the specified resource (bundled or relative). ~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def find_resource(resource):
    #{
        #Get the resource path for pyinstaller or fallback to cwd.
        try:
            basePath = sys._MEIPASS;
        except:
            basePath = os.path.abspath(".");
        path = os.path.join(basePath, "tools", resource);

        #Alternative bundled path.
        if(os.path.exists(path) == False):
        #{
            path = os.path.join(basePath, "bundled", resource);
        #}

        #Check for the resources existence.
        sys.stdout.write("Checking for resource '"+ CYAN + resource + RESET + "'... ");
        if (os.path.exists(path)):
        #{
            #Exists.
            print GREEN + "found" + RESET + ".";
            return path;
        #}
        else:
        #{
            #Doesn't exist.
            autodoc.error = True;
            print RED + "NOT found" + RESET + ".";
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~ Backs up a file and adds it to a list for later reversal. ~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_backup(filename):
    #{
        try:
        #{
            #Check if an older backup exists and remove.
            if (os.path.exists(filename+".bak")):
            #{
                os.remove(filename+".bak");
            #}

            #Move backup in place.
            shutil.copy(filename, filename+".bak");
            autodoc.backupList += [filename];
            return True;
        #}
        except Exception as e:
        #{
            print CYAN + filename + RED + ":" + RED + " Failed to backup binary (" + e.strerror + ")!";
            autodoc.escalate_admin();
            return False;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~ Moves the specified backup back to its original location. ~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def reverse_backup(filename):
    #{
        try:
        #{
            #Rename the file.
            #This is a fix for in use files and also race conditions in deletion
            #introduced by the "FILE_SHARE_DELETE" state on windows.
            tempFilename = filename + "." + str(time.time());
            shutil.move(filename, tempFilename);

            #Move backup back in place.
            shutil.move(filename + ".bak", filename);

            #Remove modified binary.
            os.remove(tempFilename);

            return True;
        #}
        except Exception as e:
        #{
            if os.name == "nt":
            #{
                try:
                #{
                    #Work around for in-use windows files.
                    import win32file
                    import win32api

                    #Schedule it for deletion on reboot.
                    win32file.MoveFileEx(tempFilename, None, win32file.MOVEFILE_DELAY_UNTIL_REBOOT);

                    return True;
                #}
                except Exception as e:
                #{
                    print CYAN + filename + RED + ":" + RED + " Failed to move backup in place (" + e.strerror + ")!";
                    return False;
                #}
            #}
            else:
            #{
                print CYAN + filename + RED + ":" + RED + " Failed to move backup in place (" + e.strerror + ")!";
                autodoc.escalate_admin();

                #Set the path to the current directory.
                os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])));
                return False;
            #}
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~ Moves all backups back to their original location. ~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def reverse_backups(bPrintInfo=False):
    #{
        #Grab the length of the list.
        length = len(autodoc.backupList);

        #Deep copy list.
        tempBackupList = list(autodoc.backupList);
        for filename in autodoc.backupList:
        #{
            #Print information if specified.
            if(bPrintInfo):
                print CYAN + filename + RED + ":" + RESET + " Reversing backup...";

            #Reverse the backup.
            if(autodoc.reverse_backup(filename)):
            #{
                #Remove from backup list on success.
                tempBackupList.remove(filename);
            #}
        #}

        #Print information if specified.
        if(bPrintInfo and length > 0):
        #{
            display.separator();
        #}

        #Move over the new list (should be empty unless failure occurred).
        autodoc.backupList = tempBackupList;
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~ Creates an autodoc task to run on system startup. ~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def create_task():
    #{
        print "Scheduling task...";

        #Get executable path and name combination.
        if(hasattr(sys, "frozen")):
            #Running from an executable.
            executable = os.path.join(os.getcwd(), sys.executable);
        else:
            #Not running from an executable.
            executable = os.path.join(os.getcwd(), __file__);

        #Make taskname.
        taskName = "Auto-Doc Healer [" + os.path.basename(os.getcwd()) + "]";

        print
        #Schedule task.
        retCode = subprocess.Popen("schtasks /Create /F /TN \""+ taskName + "\" /TR \"'" + executable + "' --silent\" /SC ONSTART /RU " + getpass.getuser() + " /RP").wait();

        #Check for error creating task.
        if(retCode != 0):
        #{
            autodoc.error = True;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~ Deletes any autodoc task scheduled to run. ~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def delete_task():
    #{
        print "Deleting task...";

        #Make taskname.
        taskName = "Auto-Doc Healer [" + os.path.basename(os.getcwd()) + "]";

        print
        #Delete task.
        CREATE_NO_WINDOW=0x08000000;
        subprocess.Popen("schtasks /Delete /F /TN \""+ taskName, creationflags=CREATE_NO_WINDOW).wait();
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~ Checks if the specified arguments were passed to the application. ~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def check_argument(*arguments):
    #{
        for argument in arguments:
        #{
            #different types of prefixes to check for.
            dash = "-" + argument;
            ddash = "--" + argument;
            fslash = "/" + argument;
            bslash = "\\" + argument;

            #Check for args and return the index if found.
            if (dash in sys.argv):
                return sys.argv.index(dash);
            if (ddash in sys.argv):
                return sys.argv.index(ddash);
            if (fslash in sys.argv):
                return sys.argv.index(fslash);
            if (bslash in sys.argv):
                return sys.argv.index(bslash);
        #}
        return False;
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~ Checks for built in autodoc arguments. Ran after Setup(). ~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def check_arguments():
    #{
        #Note: We check whether we are simulating in setup() as we use it to modify
        #      behavior prior to this call.
        #      We specify help info to be displayed there also.

        #Check for whether are reversing backups or not.
        if (autodoc.check_argument("rev", "reverse", "revert")):
        #{
            autodoc.reversing = True;
        #}

        #Check for whether are trying to be silent.
        if (autodoc.check_argument("sil", "silent")):
        #{
            autodoc.enableSilence = True;
        #}

        if (autodoc.enableService):
        #{
            #Check for whether are trying to be create a startup task.
            if (autodoc.check_argument("cretask", "createtask")):
            #{
                autodoc.create_task();
                print;
                autodoc.exit();
            #}

            #Check for whether are trying to delete a startup task.
            if (autodoc.check_argument("deltask", "deletetask")):
            #{
                autodoc.delete_task();
                autodoc.exit();
            #}
        #}

        for item in autodoc.arguments:
        #{
            if (autodoc.check_argument(item[0])):
            #{
                item[1]();
            #}
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~ Adds a function to be run before arguments are handled. ~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_preSetupCode(function):
    #{
        autodoc.preSetupCode += [function];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~ Adds a function to be run after arguments are handled. ~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_postSetupCode(function):
    #{
        autodoc.postSetupCode += [function];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~ Adds an new argument and the specified function for it. ~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_argument(argument, function):
    #{
        autodoc.arguments += [[argument, function]];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~ Adds a help message to be displayed when the help switch is called. ~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_helpInfo(info):
    #{
        autodoc.helpInfo += [info];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~ Setup code that runs prior to any other code. ~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def setup(enableService=False, enableSilence=False, enableSimulation=False):
    #{
        #Print the title block.
        display.version();

        #Defaults.
        autodoc.enableService    = enableService;
        autodoc.enableSimulation = enableSimulation;
        autodoc.enableSilence    = enableSilence;

        #Check for whether are simulating or not.
        if (autodoc.check_argument("sim", "simulate")):
        #{
            autodoc.enableSimulation = True;
        #}

        #Print stage info for debugging purposes.
        if(autodoc.enableSimulation):
        #{
            print RED + "~~~~~~~~~~" + WHITE + " Setup Stage " + RED + "~~~~~~~~~~\n" + RESET;
        #}

        retCode = 0;

        #Check if the temp directory exists. If not then the CWD isn't writable.
        if(tempdir() != None):
        #{
            #Work around for the virtualstore UAC nonsense. We can detect
            #whether we have write access to the real 'Program Files' this way.
            if (os.name == "nt"):
            #{
                CREATE_NO_WINDOW=0x08000000;
                retCode = subprocess.Popen("cmd /C cd " + tempdir(), creationflags=CREATE_NO_WINDOW).wait();
            #}
            else:
            #{
                #We should never hit this, but just in case.
                if (not os.path.exists(tempdir())):
                #{
                    retCode = -1;
                #}
            #}
        #}
        else:
        #{
            retCode = -1;
        #}

        if (retCode != 0):
        #{
            display.warning("You don't have write permission for this directory (" + os.getcwd() + "), aborting...\n");
            autodoc.exit();
        #}

        #Check for the help argument - before doing anything.
        if (autodoc.check_argument("help", "?", "info")):
        #{
            #Display help info.
            display.info("To see this help message,\n\t use the '" + CYAN + "--help" + RESET + "' or '" + CYAN + "--info" + RESET + "' or '" + CYAN + "--?" + RESET + "' switch.\n");

            display.info("To replace hacked binaries with their backups,\n\t use the '" + CYAN + "--rev" + RESET + "' or '" + CYAN + "--reverse" + RESET + "' or '" + CYAN + "--revert" + RESET + "' switch.\n");

            display.info("To simulating hacking without applying changes,\n\t use the '" + CYAN + "--sim" + RESET + "' or '" + CYAN + "--simulate" + RESET + "' switch.\n");

            display.info("To run non-interactively,\n\t use the '" + CYAN + "--sil" + RESET + "' or '" + CYAN + "--silent" + RESET + "' switch.\n");

            if (autodoc.enableService):
            #{
                display.info("To schedule Auto-Doc to run on system startup,\n\t use the '" + CYAN + "--cretask" + RESET + "' or '" + CYAN + "--createtask" + RESET + "' switch.\n");

                display.info("To remove Auto-Doc from running on system startup,\n\t use the '" + CYAN + "--deltask" + RESET + "' or '" + CYAN + "--deletetask" + RESET + "' switch.\n");
            #}

            #Display user specified help info.
            for item in autodoc.helpInfo:
                display.info(item);

            autodoc.exit();
        #}

        #Run any code that was specified to be run before arguments.
        for item in autodoc.preSetupCode:
            item();

        #Check arguments.
        autodoc.check_arguments();

        #Run any code that was specified to be run after arguments.
        for item in autodoc.postSetupCode:
            item();
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~ Teardown code ran after processing the last binary. ~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def teardown():
    #{
        #Print stage info for debugging purposes.
        if(autodoc.enableSimulation):
        #{
            print RED + "~~~~~~~~~" + WHITE + " Teardown Stage " + RED + "~~~~~~~~\n" + RESET;
        #}

        if (not autodoc.reversing and not autodoc.enableSimulation
            and autodoc.found and not autodoc.error):
        #{
            #Run any code that was specified to be run pre-teardown.
            for item in autodoc.preTeardownCode:
                item();
        #}

        if (autodoc.reversing):
        #{
            #If reversing, move the backups back into the regular location.
            autodoc.reverse_backups(True);
        #}
        elif (autodoc.enableSimulation):
        #{
            #If simulating, move the backups back into the regular location.
            autodoc.reverse_backups();
        #}
        #
        elif( autodoc.enableService and not autodoc.enableSilence
              and not autodoc.error and autodoc.found and os.name == "nt"):
        #{
            try:
                userInput = raw_input("Do you want to schedule " + CYAN + "Auto" + RED + "-" + CYAN + "Doc" + RESET + " to be run \nas a Windows Task on system startup? [no] ");
            except:
                userInput = "";
                pass; #fix crash issues with ctrl-C and ctrl-Z on windows.

            if("yes" == userInput.lower()):
            #{
                autodoc.create_task();
            #}

            display.separator();
        #}

        #Check if errors occurred at any point.
        if (autodoc.error):
        #{
            #Reverse backups and print info.
            autodoc.reverse_backups(True);
            display.warning("An error occurred...\n");
        #}

        if (autodoc.found and not autodoc.error):
        #{
            #Run any code that was specified to be run post-teardown.
            for item in autodoc.postTeardownCode:
                item();
        #}

        #check if any binaries were found and whether errors occurred.
        if(autodoc.found and not autodoc.error):
        #{
            #Success

            display.info("Everything appears to have gone successfully!");
            print    RED +  "\t\t         ::."
            print    WHITE +  "\t\t  (\\./)  .-\"\"-."
            print            "\t\t   `\\'-'`      \\"
            print              "\t\t     '.___" + YELLOW + "," + WHITE + "_" + RED + "^" + WHITE + "__/" + RESET;
            print "\t You may have to logout or reboot...\n"
        #}

        #Check if any binaries were found.
        if (not autodoc.found):
            display.warning("No binaries with matching names found...\n");

        autodoc.exit();
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~ Adds a function to run just before teardown checks. ~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_preTeardownCode(function):
    #{
        autodoc.preTeardownCode += [function];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~ Adds a function to run just before exit ~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_postTeardownCode(function):
    #{
        autodoc.postTeardownCode += [function];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~ Deletes the temp directory and exits. Use this to exit. ~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def exit():
    #{
        try:
        #{
            #try to delete the temp directory.
            shutil.rmtree(tempdir());
        #}
        except:
        #{
            #Failed, we shouldn't get here.
            pass;
        #}

        #Check if we are in silent mode before asking for input.
        if(not autodoc.enableSilence):
        #{
            try:
                raw_input("Press Enter to exit...");
            except:
                pass; #fix crash issues with ctrl-C and ctrl-Z on windows.
        #}
        sys.exit();
    #}
#}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~~~~~~~~~~~~~~ Class to handle operations related to binaries. ~~~~~~~~~~~~~~~
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class binary:
#{
    prologueCode = []; #Functions to be run before hacking a binary.
    epilogueCode = []; #Functions to be run after hacking a binary.
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~ Initializes the binary class, checks for existence and backups. ~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, filename, rename=False, copyDir=False, forceReplaceBackup=False):
    #{
        self.filename           = filename;
        self.rename             = rename;
        self.copyDir            = copyDir;
        self.forceReplaceBackup = forceReplaceBackup;

        #Check if we exist.
        if (os.path.exists(self.filename)):
        #{
            #Get version.
            self.version = self.get_version();
            self.buffer = None;
            self.error = False;
            self.hasBackup = False;

            #Check if we are a backup binary.
            if (rename == False and copyDir == False
                and not self.filename.endswith(".bak")):
            #{
                #Not a backup - check if we have a corresponding backup binary .
                backup = binary(self.filename + ".bak");
                if (not backup.error):
                #{
                    #We do - check if it is for the same version as we are.
                    if(not self.compare_version(backup)):
                    #{
                        #It is the same version.
                        self.hasBackup = True;
                    #}
                #}
            #}
        #}
        else:
        #{
            self.error = True;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~ Gets the version of a binary. ~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_version(self):
    #{
        try:
        #{
            import win32api;
            info = win32api.GetFileVersionInfo(self.filename, "\\");
            ms = info["FileVersionMS"];
            ls = info["FileVersionLS"];
            #Return version.
            return win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls);
        #}
        except:
        #{
            #No version specified or not windows.
            return 0,0,0,0;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~ Checks if the version of 'self' is newer than 'other'. ~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def compare_version(self, other):
    #{
        #Check if self is newer.
        if (self.version[0] > other.version[0]):
            return 1;
        elif (self.version[0] == other.version[0] and self.version[1] > other.version[1]):
            return 1;
        elif (self.version[0] == other.version[0] and self.version[1] == other.version[1] and self.version[2] > other.version[2]):
            return 1;
        elif (self.version[0] == other.version[0] and self.version[1] == other.version[1] and self.version[2] == other.version[2] and self.version[3] > other.version[3]):
            return 1;

        #Check if other is newer.
        if (self.version[0] < other.version[0]):
            return -1;
        elif (self.version[0] == other.version[0] and self.version[1] < other.version[1]):
            return -1;
        elif (self.version[0] == other.version[0] and self.version[1] == other.version[1] and self.version[2] < other.version[2]):
            return -1;
        elif (self.version[0] == other.version[0] and self.version[1] == other.version[1] and self.version[2] == other.version[2] and self.version[3] < other.version[3]):
            return -1;

        #Same version if the version numbers actually exist.
        ##if (self.version != (0,0,0,0) and other.version != (0,0,0,0)):
        ##    return 0;

        #fall back to time check
        ##if (self.version == (0,0,0,0) and other.version == (0,0,0,0)):
        return self.compare_time(other);
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~ Checks if the time of 'self' is newer than 'other'. ~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def compare_time(self, other):
    #{
        #Get the time.
        os.stat_float_times(False);

        newTime = os.path.getmtime(self.filename);
        oldTime = os.path.getmtime(other.filename);

        #Compare the time.
        if(newTime > oldTime):
            return 1; #newer.
        elif (newTime < oldTime):
            return -1; #older.
        else:
            return 0; #same.
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~ Opens the file associated with 'self' and writes it to the buffer. ~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def read_file(self):
    #{
        if (self.error):
            return;

        #open the binary and read it into a buffer.
        file = open(self.filename, "rb");
        self.buffer = bytearray(file.read());
        file.close();
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~ Opens the file associated with 'self' and writes the buffer to it. ~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def write_file(self):
    #{
        if (self.error):
            return;

        #Check if we are copying the binary or backing it up.
        if (self.copyDir == False and self.rename == False):
        #{
            #Add backup, error out on creation failure.
            print CYAN + self.filename + RED + ":" + RESET + " Creating backup binary...";
            if(not autodoc.add_backup(self.filename)):
            #{
                self.error = True;
                return;
            #}
        #}
        else:
        #{
            #Add copy, error out on creation failure.
            print CYAN + self.filename + RED + ":" + RESET + " Creating copy of binary...";
            try:
            #{
                path = "";
                filename = self.filename;

                if (self.copyDir != False):
                #{
                    #Create directories for the copy.
                    if(not os.path.exists(self.copyDir)):
                        os.makedirs(self.copyDir);
                    path = self.copyDir + "\\";
                #}

                #rename.
                if (self.rename != False):
                    filename = self.rename;

                #Copy.
                shutil.copy(self.filename, path + filename);

                #Set filename to copied binary.
                self.filename = path + filename;
            #}
            except Exception as e:
            #{
                print CYAN + self.filename + RED + ":" + RED + " Failed to copy binary (" + str(e) + ")!";
                autodoc.escalate_admin();
                self.error = True;
                return;
            #}
        #}

        #Write the new binary.
        print CYAN + self.filename + RED + ":" + RESET + " Creating patched binary...";
        try:
        #{
            file = open(self.filename, "wb+");
            file.write(self.buffer);
            file.flush();            #make sure the file is flushed to disk.
            os.fsync(file.fileno()); #
            file.close();
        #}
        except Exception as e:
        #{
            print CYAN + self.filename + RED + ":" + RED + " Failed to write binary (" + e.strerror + ")!";
            autodoc.escalate_admin();
            self.error = True;
            return;
        #}

        if (self.copyDir == False and self.rename == False):
        #{
            #Fix date and permission bits from the backup.
            try:
                shutil.copystat(self.filename + ".bak", self.filename);
            except:
                try:
                    sb = os.stat(self.filename + ".bak");
                    os.utime(self.filename, (sb.st_atime, sb.st_mtime));
                except:
                    autodoc.escalate_admin();
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~ Searches for a matching pattern and returns the location. ~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     regex:  The compiled regex to match with.
    #     Note:   Operates on the buffer associated with 'self'.
    def search(self, pattern):
    #{
        if (self.error):
            return;

        #initialize.
        i = 0;                     #Iterator.

        #Grab pattern information.
        regex   = re.compile(pattern, re.DOTALL);

        #Check how many matches we have for this pattern.
        list = regex.findall(self.buffer);

        #Check for no or multiple matches.
        if (len(list)) == 0:
        #{
            print CYAN + self.filename + RED + ":" + RED + " Error, missing segment" + RESET + "!";
            self.error = True;
            return 0;
        #}
        elif (len(list) > 1):
        #{
            print CYAN + self.filename + RED + ":" + RED + " Error, incorrect segment count" + RESET + "!";
            self.error = True;
            print list
            return 0;
        #}

        #Return the start of the match.
        match = regex.search(self.buffer);
        return match.start(0);
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~ Searches for matching patterns and modifies memory segments. ~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     regex:  The compiled regex to match with.
    #     offset: The offset into the matched text to start replacal at.
    #     bytes:  The bytes to replace the match[offset] with.
    #     Note:   Operates on the buffer associated with 'self'.
    def modify(self, tuple, allowedDuplicateCount=1, ignoredDuplicates=None, memset=None, offsetRange=None):
    #{
        if (self.error):
            return;

        #initialize.
        currentDuplicateCount = 0; #Amount of duplicate matches we've found.
        bFoundMatch = False;       #Whether we've found a match.
        i = 0;                     #Iterator.

        # Make single items into a list with a single item
        try:
            iter(allowedDuplicateCount)
        except:
            allowedDuplicateCount = [allowedDuplicateCount]

        #Loop through the specified tuple of patterns.
        while (i<len(tuple)):
        #{
            #Grab pattern information.
            regex   = re.compile(tuple[i], re.DOTALL);
            offset  = tuple[i+1];
            bytes   = tuple[i+2];

            #increment.
            i += 3;

            #Check how many matches we have for this pattern.
            list = regex.findall(self.buffer);

            #continue on zero matches.
            if (len(list)) == 0:
                continue;

            #Found atleast one match.
            bFoundMatch = True;

            #Iterate through all matches replacing bytes.
            #Check if only the specified ranged should be search.
            if(offsetRange == None):
            #{
                previousPosition = -1;
                endPosition = sys.maxint;
            #}
            else:
            #{
                previousPosition = offsetRange[0];
                endPosition = offsetRange[1];
            #}
            for match in regex.finditer(self.buffer):
            #{
                if (match.start(0) >= previousPosition and
                    match.start(0) < endPosition):
                #{
                    if (ignoredDuplicates == None
                        or (currentDuplicateCount+1) not in ignoredDuplicates):
                    #{
                        self.write_segment(match, offset, bytes, memset);
                        previousPosition = match.start(0)+offset+len(bytes);
                    #}
                    currentDuplicateCount += 1;
                #}
            #}
        #}

        #error if no match was found or the count of found matches was off.
        if (not bFoundMatch):
        #{
            print CYAN + self.filename + RED + ":" + RED + " Error, missing segment" + RESET + "!";
            self.error = True;
        #}
        elif (-1 not in allowedDuplicateCount and currentDuplicateCount not in allowedDuplicateCount):
        #{
            print CYAN + self.filename + RED + ":" + RED + " Error, incorrect segment count" + RESET + "!";
            self.error = True;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~ Insert at a segment with the specified byte sequence. ~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ###def insert_segment(self, match, offset, bytes):
    ####{
    ###    if (self.error):
    ###        return;
    ###
    ###    positionToModify = match.start(0) + offset;
    ###    modifiedBytes = '';
    ###    originalBytes = '';
    ###
    ###    #insert the bytes
    ###    for index, byte in enumerate(bytes):
    ###    #{
    ###        #Record changes for printing.
    ###        modifiedBytes += "%02X" % ord(byte);
    ###
    ###        #Actually do changes.
    ###        self.buffer.insert(positionToModify+index, byte);
    ###    #}
    ###
    ###    print CYAN + self.filename + RED + ":" + RESET + " Inserting at address " + YELLOW + "0x%02X" % positionToModify + RESET + " ==> " + CYAN + "0x" + modifiedBytes + RESET + ".";
    ####}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~ Writes a segment with the specified byte sequence at the ~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~ specified match + offset. ~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def write_segment(self, match, offset, bytes, memset):
    #{
        if (self.error):
            return;

        modifiedBytes = '';
        originalBytes = '';

        #Check if memset is enabled.
        if (memset != None):
        #{
            #Check and convert memset into string.
            if (type(memset) is int) : memset = chr(memset);

            #Mod the start of match to the memset value.
            while(offset > 0):
            #{
                bytes = memset + bytes;
                offset -= 1;
            #}

            #Mod the end of the match to the memset value.
            while(match.start(0)+len(bytes) < match.end(0)):
            #{
                bytes = bytes + memset;
            #}
        #}

        #modify the bytes
        positionToModify = match.start(0) + offset;
        for index, byte in enumerate(bytes):
        #{
            #Record changes for printing.
            originalBytes += "%02X" % self.buffer[positionToModify+index];
            modifiedBytes += "%02X" % ord(byte);

            #Actually do changes.
            self.buffer[positionToModify+index] = byte;
        #}

        print CYAN + self.filename + RED + ":" + RESET + " Modifying address " + YELLOW + "0x%02X" % positionToModify + RESET + " from " + CYAN + "0x" + originalBytes + RESET + " ==> " + CYAN + "0x" + modifiedBytes + RESET + ".";
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~ Runs prior to hacking the binary associated with 'self'.  ~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #Note: returns false if hacking doesn't actually occur and True otherwise.
    def prologue(self):
    #{
        #Check for error before doing anything - file doesn't exist if we hit here.
        if(self.error):
            return False;

        #Run any user code that was specified to be run before hacking the binary.
        for item in binary.prologueCode:
            item(self);

        #Print stage info for debugging purposes.
        if(autodoc.enableSimulation):
        #{
            print RED + "~~~~~~~~" + WHITE + " Prologue Stage " + RED + "~~~~~~~~~\n" + RESET;
        #}

        autodoc.found = True;

        #Check for backups and whether we are attempting to reverse them.
        if (not autodoc.reversing and self.hasBackup and not self.forceReplaceBackup):
        #{
            #Already exists.
            print CYAN + self.filename + RED + ":" + RESET + " Backup binary already exists...";
            display.separator();
            return False;
        #}
        elif (autodoc.reversing and self.hasBackup):
        #{
            #Add to backup list.
            autodoc.backupList += [self.filename];
            return False;
        #}
        elif (autodoc.reversing and not self.hasBackup):
        #{
            #No backup and reversing, do nothing.
            return False;
        #}
        elif (not autodoc.reversing and (not self.hasBackup or self.forceReplaceBackup) ):
        #{
            #Print stage info for debugging purposes.
            if(autodoc.enableSimulation):
            #{
                print RED + "~~~~~~" + WHITE + " Modification Stage " + RED + "~~~~~~~\n" + RESET;
            #}

            #Read the file into memory.
            print CYAN + self.filename + RED + ":" + RESET + " Attempting modifications...";
            self.read_file();

            return True;
        #}
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~ Runs after the hacking of the binary associated with 'self'.  ~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def epilogue(self):
    #{
        #Print stage info for debugging purposes.
        if(autodoc.enableSimulation):
        #{
            print RED + "\n~~~~~~~~" + WHITE + " Epilogue Stage " + RED + "~~~~~~~~~\n" + RESET;
        #}
        self.write_file();

        #Check if errors occurred during hacking.
        if(not self.error):
        #{
            #Run any user code that was specified to be run before after the binary.
            for item in binary.epilogueCode:
                item(self);

            #Success!
            display.success(self.filename);
        #}
        else:
        #{
            #Overall hacking failure.
            autodoc.error = True;

            #:-(
            display.abort(self.filename);
        #}

        display.separator();
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~ Adds a function to run prior to modifying a binary. ~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_prologueCode(function):
    #{
        binary.prologueCode += [function];
    #}

    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ##~~~~~~~~~~~~ Adds a function to run after modifying a binary. ~~~~~~~~~~~~
    ##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @staticmethod
    def add_epilogueCode(function):
    #{
        binary.epilogueCode += [function];
    #}
#}

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~~~~~~~~~~~~~~~~~~~~ Class to handle printing messages. ~~~~~~~~~~~~~~~~~~~~~~
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class display:
#{
    #Print Program Version
    @staticmethod
    def version():
    #{
        print RED + "======" + WHITE + "=====================" + RED + "======" + RESET;
        print RED + "====" + WHITE + "====" + CYAN + " Auto" + RED + "-" + CYAN + "Doc" + YELLOW + " v7.11 " + WHITE + "=====" + RED + "====";
        print RED + "======" + WHITE + "=====================" + RED + "======" + RESET;
        print;
    #}

    #Print abort message.
    @staticmethod
    def abort(binary):
    #{
        print CYAN + binary + RED + ":" + RED + " Aborting modifications" + RESET + "!";
    #}

    #Print success message.
    @staticmethod
    def success(binary):
    #{
        print CYAN + binary + RED + ":" + GREEN + " Successfully hacked" + RESET + "!";
    #}

    #Print a warning message.
    @staticmethod
    def warning(text):
    #{
        print YELLOW + "Warning" + RED + ": " + RESET + text;
    #}

    #Print an info message.
    @staticmethod
    def info(text):
    #{
        print GREEN + "Info" + RED + ":\t " + RESET + text;
    #}

    #Print a separator
    @staticmethod
    def separator():
    #{
        print;
        print RED + "======" + WHITE + "=====================" + RED + "======" + RESET;
        print;
    #}
#}
