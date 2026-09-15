#!/usr/bin/env bash
nvidia-smi
echo ---
ps aux | grep -E 'afterlife|python' | grep -v grep | head -30
