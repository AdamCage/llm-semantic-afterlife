#!/usr/bin/env bash
set -u
ps -ef | grep -E 's12_rotate|afterlife generate' | grep -v grep || echo none
echo "==== STATUS ===="
st=runs/s12/s12-paperb-l2-mb-physics-s1-20260926T000516Z-6c25fa59/STATUS
if [ -f "$st" ]; then tr -d '\r\n' < "$st"; echo; else echo NOSTATUS; fi
echo "==== LOG TAIL ===="
tail -n 20 /home/adam/s12/mb-physics-s1.log | sed 's/\r$//'
