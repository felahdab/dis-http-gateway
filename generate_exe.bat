@echo off
setlocal enabledelayedexpansion

if exist build (
    cd  build
    echo Deleting files in %cd%
    del /Q *.* >nul 2>&1
    cd ..
) else (
    echo 'build' directory does not exist. Skipping.
)

if exist dist (
    cd dist
    echo Deleting files in %cd%
    del /Q *.* >nul 2>&1
    cd ..
) else (
    echo 'dist' directory does not exist. Skipping.
)

if exist diagramscene32.spec (
    pyinstaller -y diagramscene32.spec
) else (
    echo diagramscene32.spec not found. Aborting.
    exit /b 1
)

if exist .env (
    copy /Y .env dist\ >nul
    echo Copied .env to dist
) else (
    echo .env file not found. Skipping copy.
)
