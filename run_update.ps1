$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $python) { throw 'Python 3 was not found. Install Python 3.10+ and add it to PATH.' }
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
& $python (Join-Path $root 'update_market_book.py')
