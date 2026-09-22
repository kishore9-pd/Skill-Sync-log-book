@echo off
echo ==========================================================
echo Starting SkillSync Daily Training Logbook Python App...
echo ==========================================================
cd /d "D:\login app"
python -m pip install -r requirements.txt
set FLASK_DEBUG=false
python app.py
pause
