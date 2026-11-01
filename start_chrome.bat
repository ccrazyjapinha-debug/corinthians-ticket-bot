@echo off
title Corinthians Ticket Bot - Abrindo Chrome via CDP...
color 0F

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║   🦅  CORINTHIANS TICKET BOT — Iniciando Sessao CDP         ║
echo  ║   Conectando Chrome com perfil local (Porta 9222)            ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

REM ── Perfil do Chrome ──────────────────────────────────────────────────────
set CHROME_PROFILE=%LOCALAPPDATA%\Google\Chrome\User Data

REM ── Caminho do executavel do Chrome ───────────────────────────────────────
set CHROME_EXE=%PROGRAMFILES%\Google\Chrome\Application\chrome.exe
if not exist "%CHROME_EXE%" (
    set CHROME_EXE=%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe
)
if not exist "%CHROME_EXE%" (
    set CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
)

if not exist "%CHROME_EXE%" (
    echo  [ERRO] Google Chrome nao encontrado no sistema.
    pause
    exit /b 1
)

echo  [→] Executavel: %CHROME_EXE%
echo  [→] Perfil: %CHROME_PROFILE%
echo  [→] Porta Remote Debugging: 9222
echo.

REM ── Fecha instancias anteriores para liberar o lock do perfil ─────────────
echo  [→] Encerrando instancias anteriores do Chrome (se houver)...
taskkill /F /IM chrome.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

REM ── Inicia o Chrome com Remote Debugging habilitado ───────────────────────
echo  [→] Abrindo Chrome com Chrome DevTools Protocol (CDP)...
start "" "%CHROME_EXE%" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="%CHROME_PROFILE%" ^
    --profile-directory=Default ^
    --no-first-run ^
    --no-default-browser-check ^
    https://www.fieltorcedor.com.br

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║  ✅ Chrome iniciado com Remote Debugging na porta 9222       ║
echo  ║                                                              ║
echo  ║  PROXIMOS PASSOS:                                            ║
echo  ║  1. Confirme sua sessao no navegador aberto                  ║
echo  ║  2. Em outro terminal, execute: python main.py               ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
pause >nul
