$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) {
  $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
  if (Test-Path $bundledPython) { $python = $bundledPython }
}
if (-not $python) { throw 'Python 3 was not found. Install Python 3.10+ and add it to PATH.' }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$desktop = [Environment]::GetFolderPath('Desktop')
$briefDir = Join-Path $desktop 'Market Briefs'
New-Item -ItemType Directory -Force -Path $briefDir | Out-Null
& $python (Join-Path $root 'update_market_book.py') '--brief-dir' $briefDir
