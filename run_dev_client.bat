@echo off
setlocal

set ROOT=%~dp0
cd /d "%ROOT%mod"

if "%~1"=="" (
  call .\gradlew.bat devClient
) else (
  call .\gradlew.bat devClient %*
)

exit /b %errorlevel%
