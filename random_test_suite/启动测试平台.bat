@echo off
echo ========================================
echo CIS芯片TRNG随机性测试平台
echo ========================================
echo.
echo 正在启动测试平台...
echo.

cd /d "%~dp0"
python gui_app.py

if errorlevel 1 (
    echo.
    echo 启动失败，请检查Python环境和依赖包
    echo 运行 install.bat 安装依赖
    pause
)
