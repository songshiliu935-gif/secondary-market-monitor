$ErrorActionPreference = 'Stop'
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) {
  $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (Test-Path $bundledPython) { $python = $bundledPython }
}
if (-not $python) { throw 'Python 3 was not found. Install Python 3.10+ and add it to PATH.' }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$port = 8765
$listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
  Start-Process -WindowStyle Hidden -FilePath $python -ArgumentList '-m','http.server',$port,'--bind','127.0.0.1' -WorkingDirectory $root
  Start-Sleep -Milliseconds 800
}
Start-Process 'http://127.0.0.1:8765/index.html'
