@echo off
title Theater Unified Suite Launcher
color 0b

echo =======================================================
echo           THEATER 24/7 BROADCAST SUITE
echo =======================================================
echo.
echo Choose what you want to launch:
echo.
echo [1] Launch Theater App (Desktop Window)
echo [2] Launch Theater App (Web Browser)
echo [3] Run 24/7 Automated TTS Voice Broadcast Scheduler
echo [4] Start Live Audio Internet Stream Server (http://localhost:8080)
echo [5] Authenticate Spotify Account (OAuth)
echo [6] Setup YouTube Music Authentication
echo [7] Start Studio MCP Harness (Blender + FL Studio Bridge)
echo [8] RUN ALL IN ONE (App + Scheduler + Live Radio Streamer)
echo.
set /p choice="Enter choice (1-8): "

if "%choice%"=="1" goto launch_desktop
if "%choice%"=="2" goto launch_web
if "%choice%"=="3" goto launch_scheduler
if "%choice%"=="4" goto launch_streamer
if "%choice%"=="5" goto auth_spotify
if "%choice%"=="6" goto auth_ytmusic
if "%choice%"=="7" goto launch_mcp
if "%choice%"=="8" goto launch_all
goto invalid

:launch_desktop
echo.
echo [*] Starting Theater Dashboard (Desktop Web)...
start "" http://localhost:8080
exit

:launch_web
echo.
echo [*] Starting Theater Dashboard in Browser...
start "" http://localhost:8080
exit

:launch_scheduler
echo.
echo [*] Starting 24/7 Automated TTS Incident Broadcast Scheduler...
cd /d "c:\Users\blue-\projects\theater"
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" broadcast_engine\hourly_scheduler.py
pause
exit

:launch_streamer
echo.
echo [*] Starting Live Audio Stream Server on http://localhost:8080...
cd /d "c:\Users\blue-\projects\theater"
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" radio_streamer\stream_server.py
pause
exit

:auth_spotify
echo.
echo [*] Launching Spotify OAuth Login...
cd /d "c:\Users\blue-\projects\theater"
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" vinyl\spotify_auth.py
pause
exit

:auth_ytmusic
echo.
echo [*] Launching YouTube Music Authentication Setup...
cd /d "c:\Users\blue-\projects\theater"
"C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" vinyl\ytmusic_auth.py
pause
exit

:launch_mcp
echo.
echo [*] Starting Studio MCP Harness Server...
cd /d "c:\Users\blue-\projects\theater\studio_mcp_harness"
node server.js
pause
exit

:launch_all
echo.
echo [*] Starting Live Stream Server (Background)...
cd /d "c:\Users\blue-\projects\theater"
start "Live Radio Streamer" "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" radio_streamer\stream_server.py

echo [*] Starting 24/7 Scheduler (Background)...
start "Theater Scheduler" "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe" broadcast_engine\hourly_scheduler.py

echo [*] Launching Theater 24/7 Live Dashboard...
start "" http://localhost:8080
exit

:invalid
echo Invalid choice.
pause
exit
