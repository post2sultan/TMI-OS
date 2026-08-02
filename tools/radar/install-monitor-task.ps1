param(
    [string]$Root = "O:\TMI-OS",
    [string]$TaskName = "TMI OS Radar Monitor",
    [int]$IntervalMinutes = 60
)
$ErrorActionPreference = "Stop"
if ($IntervalMinutes -lt 15) { throw "IntervalMinutes must be at least 15." }
$script = Join-Path $Root "tools\radar\run-monitor.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Polls due free TMI OS Radar feeds and sitemaps." -Force | Out-Null
Write-Host "Scheduled task '$TaskName' installed."
