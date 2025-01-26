#!/usr/bin/env bash

PID="$(cat /tmp/mkdocs.pid)"

sleep 2s

kill -s SIGTERM "$PID" && echo "Sinal enviado para '$PID' "
