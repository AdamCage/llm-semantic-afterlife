# Fast Task Scheduler entry. Restarts the WSL watchdog if it died, then one health check.
$ErrorActionPreference = "Continue"
$log = "C:\projects\llm-semantic-afterlife\runs\_ledger\s12_keepalive.log"
$dir = Split-Path $log
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
"KEEPALIVE_TRIGGER $(Get-Date -Format o)" | Add-Content -Path $log
& wsl.exe -d Ubuntu -- bash /mnt/c/projects/llm-semantic-afterlife/scripts/s12_keepalive.sh
"KEEPALIVE_TRIGGER_DONE $(Get-Date -Format o) exit=$LASTEXITCODE" | Add-Content -Path $log
exit 0
