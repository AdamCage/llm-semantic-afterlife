#!/usr/bin/env bash
# Bring the resident watchdog back if it died, then run one health check.
set -u
ROOT=/mnt/c/projects/llm-semantic-afterlife
sed -i 's/\r$//' \
  "$ROOT/scripts/s12_watchdog_once.sh" \
  "$ROOT/scripts/s12_watchdog_daemon.sh" \
  "$ROOT/scripts/s12_watchdog_launch.sh" \
  "$ROOT/scripts/s12_after_cohort.sh" || true
bash "$ROOT/scripts/s12_watchdog_launch.sh" || true
bash "$ROOT/scripts/s12_watchdog_once.sh"
