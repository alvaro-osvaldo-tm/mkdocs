#!/usr/bin/env bash

#
# End-to-end test for bug '3905'.
# Check if theres is any '
#

set -e

SITE_DIR='/tmp'
DIR_TEMPLATE="${SITE_DIR}/mkdocs_*"


function CLEAR_MKDOCS {

    # Ensure there is any old 'mkdocs' site dir

    for mkdocs_dir in $DIR_TEMPLATE; do

        if [ ! -d "$mkdocs_dir" ]; then
            continue
        fi

        rm -rf "$mkdocs_dir"
    done

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

        mkdocs "$COMMAND" --quiet &
        mkdocs_pid="$!"
        sleep 1s


        if IS_MKDOCS_DIR_CLEAN ; then

            setterm --foreground red --blink on
            printf " ERROR\n"
            setterm --default

            printf "[FATAL] Should exists a '%s' directory. The behavior failed.\n" "$DIR_TEMPLATE"

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

    if ! CLEAR_MKDOCS ; then
        printf "[FATAL] Unable to prepare test\n"
    fi

    printf "[INFO] Testing\n"


    if ! MESSAGE="Serve Behavior" COMMAND="serve"  TEST_AND_CHECK ; then
        printf "[INFO] Testing failed\n"
        exit 1
    fi

    printf "[INFO] Tests passed\n"

}
