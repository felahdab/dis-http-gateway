#!/bin/bash

rm -Rf build/
rm -Rf dist/

# pyinstaller --paths=. --hidden-import pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt5 \
# --hidden-import pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt5 \
# --hidden-import pyqtgraph.imageview.ImageViewTemplate_pyqt5 \
# diagramscene.py

#PATH='/c/Users/florian/bin:/mingw64/bin:/usr/local/bin:/usr/bin:/bin:/mingw64/bin:/usr/bin:/c/Users/florian/bin:/c/Program Files/Eclipse Adoptium/jdk-11.0.14.101-hotspot/bin:/c/Windows/system32:/c/Windows:/c/Windows/System32/Wbem:/c/Windows/System32/WindowsPowerShell/v1.0:/c/Windows/System32/OpenSSH:/c/Program Files (x86)/NVIDIA Corporation/PhysX/Common:/c/Program Files/NVIDIA Corporation/NVIDIA NvDLISR:/c/Program Files/dotnet:/c/Program Files/Microsoft SQL Server/130/Tools/Binn:/c/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn:/c/Program Files/Go/bin:/c/ProgramData/chocolatey/bin:/cmd:/c/Program Files/Docker/Docker/resources/bin:/c/ProgramData/DockerDesktop/version-bin:/c/Users/florian/scoop/shims:/c/Users/florian/AppData/Local/Programs/Python/Python39/Scripts:/c/Users/florian/AppData/Local/Programs/Python/Python39:/c/Users/florian/AppData/Local/Microsoft/WindowsApps:/c/Users/florian/.dotnet/tools:/c/Users/florian/go/bin:/c/Program Files (x86)/Nmap:/c/Program Files/heroku/bin:/usr/bin/vendor_perl:/usr/bin/core_perl'

#PATH='/c/Users/florian/bin:/mingw64/bin:/usr/local/bin:/usr/bin:/bin:/mingw64/bin:/usr/bin:/c/Users/florian/bin:/c/Program Files/Eclipse Adoptium/jdk-11.0.14.101-hotspot/bin:/c/Windows/system32:/c/Windows:/c/Windows/System32/Wbem:/c/Windows/System32/WindowsPowerShell/v1.0:/c/Windows/System32/OpenSSH:/c/Program Files (x86)/NVIDIA Corporation/PhysX/Common:/c/Program Files/NVIDIA Corporation/NVIDIA NvDLISR:/c/Program Files/dotnet:/c/Program Files/Microsoft SQL Server/130/Tools/Binn:/c/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn:/c/Program Files/Go/bin:/c/ProgramData/chocolatey/bin:/cmd:/c/Program Files/Docker/Docker/resources/bin:/c/ProgramData/DockerDesktop/version-bin:/c/Users/florian/scoop/shims:/c/Users/florian/AppData/Local/Programs/Python/Python39-32/Scripts:/c/Users/florian/AppData/Local/Programs/Python/Python39-32:/c/Users/florian/AppData/Local/Microsoft/WindowsApps:/c/Users/florian/.dotnet/tools:/c/Users/florian/go/bin:/c/Program Files (x86)/Nmap:/c/Program Files/heroku/bin:/usr/bin/vendor_perl:/usr/bin/core_perl'
pyinstaller -y diagramscene32.spec

