@echo off
REM Attach a useful-helpers instance to a target directory.
REM
REM Usage:  attach.bat <target-directory>
REM
REM You can also drag a folder from Explorer onto this file.
REM The cd below makes this release directory the working directory, which is
REM what "python -m factory" needs to import the package.

setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: attach.bat ^<target-directory^>
    exit /b 2
)

set PY=py
where py >nul 2>&1 || set PY=python

%PY% -m factory attach "%~1"
exit /b %errorlevel%
