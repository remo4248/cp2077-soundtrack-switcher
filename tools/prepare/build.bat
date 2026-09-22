@echo off
rem Builds prepare.exe, which ships with the mod and is called by rescan.bat.
rem Needs Visual Studio's C++ tools. Run from a developer prompt and it uses that;
rem otherwise it finds any installed Visual Studio through vswhere.
setlocal
set HERE=%~dp0

if defined VCINSTALLDIR goto :build
set VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe
if not exist "%VSWHERE%" (
    echo Visual Studio not found. Install "Desktop development with C++" and try again.
    exit /b 1
)
for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set VSPATH=%%i
if not defined VSPATH (
    echo No Visual Studio with the C++ tools was found.
    exit /b 1
)
call "%VSPATH%\VC\Auxiliary\Build\vcvars64.bat" >nul

:build
if not exist "%HERE%build" mkdir "%HERE%build"
rem Version metadata, so the binary says what it is and who made it. An unsigned exe with none of
rem that is what virus scanners flag by default, and a reviewer has nothing to go on either.
rc /nologo /fo "%HERE%build\prepare.res" "%HERE%prepare.rc"
if errorlevel 1 exit /b 1

rem /guard:cf and the linker flags below are the hardening a normal Windows build has; a binary
rem without them looks unusual to a scanner.
cl /nologo /std:c++20 /EHsc /O2 /MT /W3 /guard:cf /DNDEBUG /D_CRT_SECURE_NO_WARNINGS /D_USE_MATH_DEFINES ^
   /I"%HERE%deps" /I"%HERE%deps\queue" ^
   "%HERE%prepare.cpp" "%HERE%deps\ebur128.c" "%HERE%deps\stb_vorbis.c" ^
   /Fo:"%HERE%build\\" /Fe:"%HERE%build\prepare.exe" ^
   /link "%HERE%build\prepare.res" /GUARD:CF /DYNAMICBASE /NXCOMPAT /HIGHENTROPYVA
