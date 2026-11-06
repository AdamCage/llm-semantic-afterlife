#!/usr/bin/env bash
set -u
echo "==== ROTATE PROC ===="
ps -ef | grep s12_rotate | grep -v grep || echo none
echo "==== INODE ===="
ls -li /mnt/c/projects/llm-semantic-afterlife/scripts/s12_rotate.sh
pid="$(pgrep -f 'scripts/s12_rotate.sh' | head -n 1 || true)"
echo "pid=${pid:-none}"
if [ -n "${pid:-}" ]; then
  echo "==== FD ===="
  ls -l "/proc/$pid/fd" | grep s12_rotate || true
  echo "==== EXE CWD ===="
  tr '\0' ' ' < "/proc/$pid/cmdline"; echo
fi
echo "==== BASH -N ===="
bash -n /mnt/c/projects/llm-semantic-afterlife/scripts/s12_watchdog_once.sh && echo watchdog_ok
bash -n /mnt/c/projects/llm-semantic-afterlife/scripts/s12_watchdog_daemon.sh && echo daemon_ok
bash -n /mnt/c/projects/llm-semantic-afterlife/scripts/s12_after_cohort.sh && echo after_ok
bash -n /mnt/c/projects/llm-semantic-afterlife/scripts/s12_rotate.sh && echo rotate_ok
