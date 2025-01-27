#!/usr/bin/env bash

#
# End-to-end test for bug '3905'.
# Check if theres is any '
#

set -e

SITE_DIR='/tmp'
DIR_TEMPLATE="${SITE_DIR}/mkdocs_*"
LOG_FILE="./test-3905.log"

function CLEAR_MKDOCS {

    # Ensure there is any old 'mkdocs' site dir

    for mkdocs_dir in $DIR_TEMPLATE; do

        if [ ! -d "$mkdocs_dir" ]; then
            continue
        fi

        rm -rf "$mkdocs_dir"
    done

    # Remove any Mkdocs instance
    pid="$(ss -ltp | grep mkdocs | grep -oE 'pid=[0-9]*' | grep -oE '[0-9]*')"

    if [ -z "$pid" ]; then
        return 0
    fi

    kill -s SIGKILL "$pid"

}

function IS_MKDOCS_DIR_CLEAN {

    # Return if there is any 'mkdocs' site dir

    # shellcheck disable=SC2317
    for mkdocs_dir in $DIR_TEMPLATE; do

        if [ ! -d "$mkdocs_dir" ]; then
            continue
        fi

        return 1
    done

}


function TEST_AND_CHECK {

    COMMAND="${COMMAND}"
    MESSAGE="${MESSAGE}"
    SIGNALS="${SIGNAL:=SIGTERM SIGINT SIGHUP SIGUSR1 SIGUSR2 SIGQUIT}"

    failed=0

    for signal in $SIGNALS; do

        printf " » '%-16s' with signal '%-8s' ... " "$MESSAGE" "$signal"

        CLEAR_MKDOCS

        mkdocs "$COMMAND" 2>> "$LOG_FILE" >> "$LOG_FILE" &
        mkdocs_pid="$!"
        sleep 1s


        if IS_MKDOCS_DIR_CLEAN ; then

            setterm --foreground red --blink on
            printf " ERROR\n"
            setterm --default

            printf "[FATAL] Should exists a '%s' directory. The behavior failed.\n" "$DIR_TEMPLATE"
            exit 1

        fi

        kill -s "$signal" "$mkdocs_pid"
        sleep 1s

        if IS_MKDOCS_DIR_CLEAN ; then
            setterm --foreground green
            printf "PASS\n"
        else
            setterm --foreground red --blink on
            printf "FAILED\n"
            failed=1
        fi


        setterm --default
    done

    return "$failed"

}

{

    if ! (
        CLEAR_MKDOCS &&
        touch "$LOG_FILE" &&
        truncate --size 0 "$LOG_FILE"
    ); then
      printf "[FATAL] Unable to prepare test\n"
      exit 1
    fi



    printf "[INFO] Testing\n"


    if ! MESSAGE="Serve Behavior" COMMAND="serve"  TEST_AND_CHECK ; then
        printf "[INFO] Testing failed\n"
        exit 1
    fi

    printf "[INFO] Tests passed\n"

}
