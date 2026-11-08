@echo off
title CapCut offline mode OFF
net session >nul 2>&1
if errorlevel 1 (
  echo  Windows will ask for permission - click Yes.
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_files (don't touch)\offline.ps1" -Off
echo.
pause
