@echo off
echo ========================================
echo CIS芯片TRNG随机性测试套件 - 安装脚本
echo ========================================
echo.

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo.
echo 安装依赖包...
pip install numpy scipy matplotlib

echo.
echo 验证安装...
python -c "import numpy; import scipy; import matplotlib; print('依赖包安装成功!')"

echo.
echo 运行测试验证...
python test_tool.py

echo.
echo 安装完成！
echo.
echo 使用方法:
echo   1. 准备测试数据文件放入 data 目录
echo   2. 运行: python main.py --data-dir ./data
echo   3. 查看 reports 目录下的测试报告
echo.
pause
