@echo off
chcp 65001 >nul
echo ========================================
echo CIS芯片TRNG随机性测试
echo ========================================
echo.

cd /d "%~dp0"
python run_test.py

pause
