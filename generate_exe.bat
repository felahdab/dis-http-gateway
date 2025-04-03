cd build
del /Q *.*
cd ..

cd dist
del /Q *.*
cd ..

pyinstaller -y diagramscene32.spec

copy .env dist