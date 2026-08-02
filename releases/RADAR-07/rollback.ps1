param([string]$Root = "O:\TMI-OS", [Parameter(Mandatory)][string]$PreviousReleaseTag, [string]$EnvFile = "O:\TMI-OS\docker\.env.production.local")
& (Join-Path $Root "scripts\rollback-release.ps1") -Root $Root -EnvFile $EnvFile -PreviousReleaseTag $PreviousReleaseTag -Environment production -ApproveProduction
