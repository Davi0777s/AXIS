# Builds AXIS-Setup.exe (one-file installer) with PyInstaller.
# Requires: pip install pyinstaller
$ErrorActionPreference = "Stop"
python -m PyInstaller --noconfirm installer\installer.spec
if (Test-Path -LiteralPath "dist_installer") { }
New-Item -ItemType Directory -Path "dist_installer" -Force | Out-Null
Move-Item -LiteralPath "dist\AXIS-Setup.exe" -Destination "dist_installer\AXIS-Setup.exe" -Force
Get-Item -LiteralPath "dist_installer\AXIS-Setup.exe" | Select-Object FullName, @{N="MB";E={[math]::Round($_.Length/1MB,1)}}