# Task Scheduler entry. The first line is written even if WSL is down,
# so a missed hour is visible in this file.
$ErrorActionPreference = "Continue"
$log = "C:\projects\llm-semantic-afterlife\runs\_ledger\s12_hourly.log"
$dir = Split-Path $log
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
"HOURLY_TRIGGER $(Get-Date -Format o)" | Add-Content -Path $log
& wsl.exe -d Ubuntu -- bash /mnt/c/projects/llm-semantic-afterlife/scripts/s12_hourly.sh
"HOURLY_TRIGGER_DONE $(Get-Date -Format o) exit=$LASTEXITCODE" | Add-Content -Path $log
exit 0
