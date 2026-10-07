$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$taskName = 'Secondary Market Monitor - Daily Market Book'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $root 'run_update.ps1') + '"')
$trigger = New-ScheduledTaskTrigger -Daily -At 8:30AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Updates the English Market Book after the US market close.' -Force | Out-Null
Write-Output "Registered: $taskName"
