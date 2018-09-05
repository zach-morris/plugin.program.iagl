REM This script was taken from the ROM Collection Browser
REM All credit goes to malte
echo off
Title Running %*

REM Set Variables
set KodiLaunchCmd="%PROGRAMFILES%\Kodi\Kodi.exe"
REM Check for portable mode

echo Stopping Kodi...
echo.
taskkill /f /IM Kodi.exe>nul 2>nul

REM Give it a second to quit
cscript //B //Nologo "%~dp0\Sleep.vbs" 1
echo Starting %*...
echo.
%*

REM Restart Kodi
echo Restarting Kodi...
echo cscript //B //Nologo "%~dp0\LaunchKODI.vbs" %KodiLaunchCmd%
cscript //B //Nologo "%~dp0\LaunchKODI.vbs" %KodiLaunchCmd%