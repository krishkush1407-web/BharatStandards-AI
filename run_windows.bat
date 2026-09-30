@echo off
title BharatStandards AI - SIH26108
cd /d "%~dp0"
py -3 -m venv .venv 2>nul
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
pause
