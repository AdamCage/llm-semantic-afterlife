#!/usr/bin/env bash
set -u
kill -TERM 621 2>/dev/null || true
sleep 1
ps -ef | grep s11_watch_matrix | grep -v grep || echo "no watchers"
ps -ef | grep "afterlife generate" | grep -v grep || echo "no generate"
