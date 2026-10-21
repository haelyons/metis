#!/usr/bin/env bash
# box.sh: run one command on the held box over ssh (the fixer's only tool). usage: box.sh <command...>
exec ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o ServerAliveInterval=30 -i $HOME/.ssh/lambda_ed25519 ubuntu@129.80.201.128 "$*"
