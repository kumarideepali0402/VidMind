@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
REM No --reload: long analysis jobs are stored in memory and are lost on reload.
python -m uvicorn api:app --host 127.0.0.1 --port 8000
