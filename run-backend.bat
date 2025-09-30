@echo off
echo Starting backend server...
cd server
call .\.venv\Scripts\activate
uvicorn main:app --reload
