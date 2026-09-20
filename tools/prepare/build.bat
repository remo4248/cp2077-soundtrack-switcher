@echo off
rem Builds prepare.exe. Ships with the mod; rescan.bat calls it. Needs Visual Studio's C++ tools.
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
set HERE=%~dp0
if not exist "%HERE%build" mkdir "%HERE%build"
cl /nologo /std:c++20 /EHsc /O2 /MT /DNDEBUG /D_CRT_SECURE_NO_WARNINGS /D_USE_MATH_DEFINES ^
   /I"%HERE%deps" /I"%HERE%deps\queue" ^
   "%HERE%prepare.cpp" "%HERE%deps\ebur128.c" "%HERE%deps\stb_vorbis.c" ^
   /Fo:"%HERE%build\\" /Fe:"%HERE%build\prepare.exe"
