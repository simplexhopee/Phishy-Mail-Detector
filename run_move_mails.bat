@echo off
SET venv_directory=C:\Users\Administrator\Documents\mail_classification_env
SET log_file=%venv_directory%\move.log

REM Clear previous log file
echo. > "%log_file%"

REM Navigate to the script directory
cd /d "%venv_directory%"

REM Activate the virtual environment
call "%venv_directory%\Scripts\activate"
echo Activated >> "%log_file%"

REM Log the arguments received
echo Arguments: %1 %2 %3 >> "%log_file%"

REM Set junk and mailbox paths
SET junk="C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\%1\Junk E-mail"
SET mailbox="C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\%2\Inbox"

REM Log the paths
echo Junk folder: %junk% >> "%log_file%"
echo Inbox folder: %mailbox% >> "%log_file%"

REM Run the Python script with passed arguments
python Move_Inbox.py %junk% %mailbox% %3 >> "%log_file%" 2>&1

REM Log script execution
echo Enterred >> "%log_file%"

REM Deactivate the virtual environment
call deactivate

REM Log deactivation
echo Deactivated >> "%log_file%"
