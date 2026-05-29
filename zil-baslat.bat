@echo off
title Zil Sistemi v1
cd /d "%~dp0"
set HTML_FILE=zil-programi-v1.html

:: HTML dosyasi kontrolu
if not exist "%HTML_FILE%" (
    for %%f in (zil-program*.html) do (
        set HTML_FILE=%%f
        echo [BILGI] zil-programi-v1.html bulunamadi, %%f kullaniliyor.
        goto :HTML_FOUND
    )
    echo [HATA] HTML dosyasi bulunamadi!
    pause & exit /b 1
)
:HTML_FOUND

:: Sunucu dosyasi kontrolu
if not exist "zunucu\sunucu.py" (
    echo [HATA] zunucu\sunucu.py bulunamadi!
    pause & exit /b 1
)

:: Python kontrolu
set PYTHON_CMD=
where python >nul 2>&1 && set PYTHON_CMD=python
if "%PYTHON_CMD%"=="" (
    where py >nul 2>&1 && set PYTHON_CMD=py
)
if "%PYTHON_CMD%"=="" (
    where pythonw >nul 2>&1 && set PYTHON_CMD=pythonw
)
if "%PYTHON_CMD%"=="" (
    echo [HATA] Python kurulu degil!
    pause & exit /b 1
)

:: Eski sunucuyu oldur
taskkill /f /fi "WINDOWTITLE eq Zil Sunucu" >nul 2>&1
wmic process where "commandline like '%%sunucu.py%%'" call terminate >nul 2>&1
timeout /t 1 /nobreak >nul

:: Eski Zil Chrome penceresini kapat
wmic process where "commandline like '%%ZilSistemi%%'" call terminate >nul 2>&1
timeout /t 1 /nobreak >nul

:: Eski port dosyasini temizle
if exist "zil-port.txt" del "zil-port.txt"

:: Firewall kurali
netsh advfirewall firewall add rule name="Zil Sistemi" dir=in action=allow protocol=TCP localport=8765-8800 >nul 2>&1

:: Sunucuyu gorulur konsol ile baslat
start "Zil Sunucu" /MIN %PYTHON_CMD% "%~dp0zunucu\sunucu.py"

:: Port dosyasinin olusmasini bekle (max 10 saniye)
set /a WAIT=0
:WAITLOOP
timeout /t 1 /nobreak >nul
set /a WAIT+=1
if exist "zil-port.txt" goto PORTFOUND
if %WAIT% GEQ 10 goto FALLBACK
goto WAITLOOP

:PORTFOUND
set /p ZIL_PORT=<zil-port.txt
echo [ZIL] Port: %ZIL_PORT%
set ZIL_URL=http://localhost:%ZIL_PORT%/%HTML_FILE%?fullscreen=1
goto LAUNCHBROWSER

:FALLBACK
echo [UYARI] Sunucu 10 saniyede baslamadi, 8765 portu deneniyor...
set ZIL_PORT=8765
set ZIL_URL=http://localhost:%ZIL_PORT%/%HTML_FILE%?fullscreen=1

:LAUNCHBROWSER
set CHROME_FLAGS=--user-data-dir="%TEMP%\ZilSistemi" --start-fullscreen --disable-session-crashed-bubble --disable-infobars --noerrdialogs

set CHROME_EXE=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe"      set CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe"       set CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe

if "%CHROME_EXE%"=="" (
    start "" "%ZIL_URL%"
    goto END
)

:: Chrome'u baslat
start "" "%CHROME_EXE%" --app="%ZIL_URL%" %CHROME_FLAGS%

:: ---------------------------------------------------------------
:: Chrome penceresini one getir: AttachThreadInput + BringWindowToTop
:: (SetForegroundWindow tek basina Windows tarafindan bloklanabiliyor)
:: Gecici PS1 dosyasi kullaniriz - tirnak kargasasini onler.
:: ---------------------------------------------------------------
set PS1=%TEMP%\zil_focus_%RANDOM%.ps1

(
echo Add-Type -TypeDefinition @'
echo using System;
echo using System.Runtime.InteropServices;
echo public class ZilFocus {
echo     [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
echo     [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
echo     [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
echo     [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
echo     [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
echo     [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool attach);
echo     [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
echo }
echo '@ -ErrorAction SilentlyContinue
echo.
echo $waited = 0
echo while ($waited -lt 10000) {
echo     Start-Sleep -Milliseconds 500
echo     $waited += 500
echo     $procs = Get-Process chrome -ErrorAction SilentlyContinue ^| Where-Object { $_.MainWindowHandle -ne 0 } ^| Sort-Object StartTime -Descending
echo     if ($procs -and $procs[0].MainWindowHandle -ne 0) {
echo         $hwnd = $procs[0].MainWindowHandle
echo         [ZilFocus]::ShowWindow($hwnd, 9) ^| Out-Null
echo         $fg    = [ZilFocus]::GetForegroundWindow()
echo         $fgTid = [ZilFocus]::GetWindowThreadProcessId($fg, [ref][uint32]0)
echo         $myTid = [ZilFocus]::GetCurrentThreadId()
echo         [ZilFocus]::AttachThreadInput($myTid, $fgTid, $true)  ^| Out-Null
echo         [ZilFocus]::BringWindowToTop($hwnd)                   ^| Out-Null
echo         [ZilFocus]::SetForegroundWindow($hwnd)                ^| Out-Null
echo         [ZilFocus]::AttachThreadInput($myTid, $fgTid, $false) ^| Out-Null
echo         break
echo     }
echo }
) > "%PS1%"

:: Gizli PowerShell penceresiyle calistir (PS konsolu odagi calmasin)
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%PS1%"
del "%PS1%" >nul 2>&1

:END
exit
