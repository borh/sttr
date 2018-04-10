#!/usr/bin/env bash

CORPORA_DIR=~/Dropbox/Complexity/Corpora
CORPORA=$(ls $CORPORA_DIR)
META="brow"

if [ -x "$(command -v parallel)" ]; then
    ls $CORPORA_DIR | parallel "python run_sttr.py ${CORPORA_DIR}/{} sttr_{} --meta ${META}"
else
    for corpus in $CORPORA; do
        python run_sttr.py "${CORPORA_DIR}/${corpus}" sttr_$corpus --meta "${META}" || exit 1
    done
fi
