@echo off
setlocal
cd /d %~dp0\..
py -3 apps\bot\discord_job_bot.py
endlocal
