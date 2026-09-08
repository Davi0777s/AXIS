# Build AXIS.exe (onedir portable folder) and assemble the runtime home.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root

python -m PyInstaller --noconfirm --clean AXIS.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$dist = Join-Path $root "dist\AXIS"
New-Item -ItemType Directory -Path $dist -Force | Out-Null

# Runtime home: these live next to the exe so find_root() and the bash helpers
# resolve them (tools/ and firmware/ are user-supplied and gitignored).
foreach ($d in @("scripts", "wifi-fix", "tools", "firmware")) {
    $src = Join-Path $root $d
    if (Test-Path -LiteralPath $src) {
        Write-Host "  + $d -> dist\AXIS"
        Copy-Item -LiteralPath $src -Destination $dist -Recurse -Force
    }
}
Copy-Item -LiteralPath (Join-Path $root "axis.toml") -Destination $dist -Force
Copy-Item -LiteralPath (Join-Path $root "assets") -Destination $dist -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $dist -Force

Pop-Location
Write-Host "Build ok: $dist\AXIS.exe"