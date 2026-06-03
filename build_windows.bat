@echo off
REM v2.0.0 Phase 4.5: Windows 一键打包 EXE
REM 主公: 在 Win 10/11 上双击此文件即可生成 汉献帝之末路.exe

chcp 65001 > nul
setlocal enabledelayedexpansion

echo ============================================
echo   汉献帝之末路 - Windows 打包脚本
echo ============================================
echo.

REM ── 1) 检查 Python ──
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+:
    echo        https://www.python.org/downloads/
    echo        安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo [1/5] Python 检测通过

REM ── 2) 创建 venv ──
if not exist "venv\" (
    echo [2/5] 正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [错误] venv 创建失败
        pause
        exit /b 1
    )
) else (
    echo [2/5] 虚拟环境已存在
)

REM ── 3) 装依赖 ──
echo [3/5] 正在安装依赖...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -e . --quiet
python -m pip install pyinstaller pywebview --quiet
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [3/5] 依赖安装完成

REM ── 4) 构建前端 (如果 web/dist 不存在) ──
if not exist "web\dist\" (
    echo [4/5] 正在构建前端...
    cd web
    if not exist "node_modules\" (
        call npm install --silent
    )
    call npm run build --silent
    cd ..
    if not exist "web\dist\" (
        echo [警告] 前端未构建, 将使用开发版
    )
) else (
    echo [4/5] 前端已构建
)

REM ── 5) 打包 EXE ──
echo [5/5] 正在打包 EXE (这可能需要 3-5 分钟)...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
pyinstaller han_empire.spec --clean
if %errorlevel% neq 0 (
    echo [错误] 打包失败, 详见上方输出
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成!
echo   输出: dist\汉献帝之末路.exe
echo ============================================
echo.
echo 下一步:
echo   1) 将 dist\汉献帝之末路.exe 复制到任意位置
echo   2) 双击即可启动游戏
echo   3) 首次启动会要求配置 API Key
echo.
pause
