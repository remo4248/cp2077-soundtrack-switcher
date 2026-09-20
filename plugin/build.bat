@echo off
rem Builds SoundtrackSwitcher.dll. Needs Visual Studio's C++ tools (see README).
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist build mkdir build
cl /nologo /std:c++20 /EHsc /O2 /MD /W3 /DNDEBUG /I"%~dp0deps\RED4ext.SDK\include" /LD "%~dp0src\main.cpp" /Fo:"%~dp0build\\" /Fe:"%~dp0build\SoundtrackSwitcher.dll" /link /DLL user32.lib
