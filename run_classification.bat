@echo off
setlocal EnableDelayedExpansion

SET email_path=%1
set msgfile=%2




REM Set the directory where your classification script is located
SET script_directory=C:\Users\Administrator\Documents\mail_classification_env\Files


REM Set the virtual environment directory
SET venv_directory=C:\Users\Administrator\Documents\mail_classification_env

REM Navigate to the script directory
cd /d "%venv_directory%"

REM Activate the virtual environment
call "%venv_directory%\Scripts\activate"

IF %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment: %venv_directory%\Scripts\activate.bat >> classify_debug.log
    exit /b 1
)


REM Set the full path to the Python executable
SET python_executable=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe

REM Navigate to the script directory
cd /d "%script_directory%"

REM Debug output to log file
echo Running classification script for %email_path% > classify_debug.log
echo Email path: %email_path% >> classify_debug.log

echo activated virtual environment: %venv_directory%\Scripts\activate.bat >> classify_debug.log

REM Run the Python classification script and capture the result
python classify_email.py "%email_path%" > classification_result.txt 2>> classify_debug.log

REM Read the classification result from the file
SET /p classification_result=<classification_result.txt

REM Debug output to log file
echo Classification result: %classification_result% >> classify_debug.log



REM Define the base path for MailEnable message storage
SET "basepath=C:\Program Files (x86)\Mail Enable\Queues\SMTP\Inbound\Messages"
SET folder_path=%basepath%

REM Log paths
echo Base path: %basepath% >> classify_debug.log
echo Folder path: %folder_path% >> classify_debug.log

REM Determine the full path to the email file
SET filepath=%folder_path%\%email_path%

REM Log the file path
echo File path: %filepath% >> classify_debug.log

SET mailbox=

SET email_address=

REM Read the email file and extract the mailbox
FOR /F "tokens=1,* delims=:" %%A IN ('type "%filepath%"') DO (
    SET header=%%A
    SET value=%%B
    REM Trim leading spaces
    SET value=!value:~1!
    echo Processing header: !header! >> classify_debug.log
    echo Processing value: !value! >> classify_debug.log
    IF /I "!header!"=="To" (
        REM Extract the mailbox from the "To" header
        SET mailbox=!value!
        echo Found To header with mailbox: !mailbox! >> classify_debug.log
        REM Extract the email address part (between < and >)
        FOR /F "tokens=2 delims=<>" %%X IN ("!mailbox!") DO (
            SET email_address=%%X
            REM Extract the local part before the @
            FOR /F "tokens=1 delims=@" %%Y IN ("!email_address!") DO (
                SET mailbox=%%Y
            )
            
        )
        GOTO found
    )
)

:found
REM Check if mailbox was found
IF NOT DEFINED mailbox (
    echo Mailbox not found in email headers. >> classify_debug.log
    exit /b 1
)
SET mailbox=C:\Program Files (x86)\Mail Enable\Postoffices\phishblock.com.ng\MAILROOT\%mailbox%\Phishy Mails

echo Mailbox: %mailbox% >> classify_debug.log

REM Debug output to log file
echo Mailbox path: %mailbox% >> classify_debug.log

REM Check if the classification result and paths are correctly set
IF "%classification_result%"=="P" (
    REM Prepend the required header to the email file
    echo X-ME-Content: Deliver-To=Junk>temp_mai_header.txt
    type "%filepath%" >> temp_mai_header.txt
    move /Y temp_mai_header.txt "%filepath%" >> classify_debug.log 2>&1
   
)
python check_ddos.py "%email_address%" "%filepath%" "%mailbox%">> classify_debug.log 2>&1

REM End of script
echo Script execution completed >> classify_debug.log
