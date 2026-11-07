#!/usr/bin/env bash
set -u
cat >> /home/adam/s12/PAUSED.txt <<'EOF'
Scheduled tasks SemanticAfterlifeS12Hourly and SemanticAfterlifeS12Watchdog are Disabled.
The WSL daemon is stopped. Do not enable them until resume is requested.
EOF
echo "==== PAUSED ===="
cat /home/adam/s12/PAUSED.txt
