@echo off
rem ============================================================
rem  AXIS launcher alt (si se invoca axis.cmd directamente).
rem  El acceso directo del escritorio usara pythonw.exe en su
rem  lugar (sin ventana de consola). Este .cmd es solo fallback.
rem ============================================================
cd /d "%~dp0"

pythonw.exe "%~dp0axis.py"
if errorlevel 1 (
  echo [ERROR] AXIS no arranco. Revisa el log en temp.
)