@echo off
setlocal enabledelayedexpansion

:: --------------------------------------
:: 1. Download WinPython
:: --------------------------------------
echo Downloading WinPython 3.10 64-bit...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/winpython/winpython/releases/download/6.1.20230527/Winpython64-3.10.11.1dot.exe' -OutFile 'Winpython64-3.10.11.1dot.exe'"

:: --------------------------------------
:: 2. Extract WinPython
:: --------------------------------------
echo Extracting WinPython...
start /wait Winpython64-3.10.11.1dot.exe

:: --------------------------------------
:: 3. Go into extracted folder
:: --------------------------------------
cd WPy64-310111

set PYTHON=%cd%\python-3.10.11.amd64\python.exe
set PIP=%cd%\python-3.10.11.amd64\Scripts\pip.exe

:: --------------------------------------
:: 4. Install only required Python packages
:: --------------------------------------
echo Installing project requirements...
%PYTHON% -m pip install -r ..\requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python dependencies. Make sure you are able to access pip repositories
    exit /b %ERRORLEVEL%
)

echo Removing unused EXE files from WinPython root...

del /f /q "Qt Assistant.exe" "Qt Designer.exe" "Qt Linguist.exe" "Spyder.exe" "Spyder reset.exe" "IPython Qt Console.exe" "IDLE (Python GUI).exe" "Jupyter Lab.exe" "Jupyter Notebook.exe" "Pyzo.exe" "VS Code.exe" "IDLEX.exe" "IDLE (Python GUI).exe"

echo Cleaning leftover folders...

rmdir /s /q settings scripts t notebooks

cd ..

:: --------------------------------------
:: 5. Create portable project folder
:: --------------------------------------
echo Creating portable project folder...

set PORTABLE=dis-http-gateway-portable

:: Clean up old folder if it exists
if exist %PORTABLE% (
    echo Removing old %PORTABLE%...
    rmdir /s /q %PORTABLE%
)
mkdir %PORTABLE%

:: Exclusion list
set EXCLUDES=.git .gitignore build_portable_version.bat Winpython64-3.10.11.1dot.exe %PORTABLE% dis-http-gateway-portable.zip _trial_temp .vscode build dist

:: Copy folders (excluding known ones)
for /d %%D in (*) do (
    set SKIP=0
    for %%E in (%EXCLUDES%) do (
        if /I "%%D"=="%%E" set SKIP=1
    )
    if !SKIP! EQU 0 (
        echo Copying folder: %%D
        xcopy "%%D" "%PORTABLE%\%%D" /E /I /Y >nul
    )
)

:: Copy top-level files (excluding known ones)
for %%F in (*) do (
    set SKIP=0
    for %%E in (%EXCLUDES%) do (
        if /I "%%F"=="%%E" set SKIP=1
    )
    if !SKIP! EQU 0 (
        echo Copying file: %%F
        copy "%%F" "%PORTABLE%\%%F" >nul
    )
)

:: Copy WinPython extracted folder explicitly
echo Copying WinPython runtime...
xcopy WPy64-310111 "%PORTABLE%\WPy64-310111" /E /I /Y >nul

:: --------------------------------------
:: 6. Create launcher inside portable folder
:: --------------------------------------
echo Creating portable launcher...
(
  echo @echo off
  :: %%~dp0 = drive + path of this script; /d allows changing drive too
  echo cd /d %%~dp0WPy64-310111 
  echo python-3.10.11.amd64\python.exe ..\app.py
  echo pause
) > %PORTABLE%\run_app.bat

@REM :: --------------------------------------
@REM :: 7. Zip the folder
@REM :: --------------------------------------
@REM echo Zipping %PORTABLE%...

@REM powershell -Command "Compress-Archive -Path '%PORTABLE%\*' -DestinationPath 'dis-http-gateway-portable.zip' -Force"

echo Done! The project is available in dis-http-gateway-portable