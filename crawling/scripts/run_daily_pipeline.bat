@echo off
setlocal
cd /d %~dp0\..
set OLLAMA_MAX_CONTENT_CHARS=3000
py -3 apps\pipeline\daily_job_pipeline.py --keyword AI --max-jobs 10 --analysis-max-jobs 10 --provider ollama --model qwen2.5:3b --report-format csv --notify console --notify discord
endlocal

