#!/usr/bin/env bash

# Remove any Mkdocs instance
pid="$(ss -ltp | grep mkdocs | grep -oE 'pid=[0-9]*' | grep -oE '[0-9]*')"


if [ -z "$pid" ]; then
    exit 0
fi

kill -s SIGKILL "$pid"
