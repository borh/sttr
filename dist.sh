#!/usr/bin/env bash

DISTDIR=~/Dropbox/Complexity/Results/2020-01

pipenv run sttr --meta author,genre,brow,narrative_perspective,year ~/Dropbox/Complexity/Corpora/ --fixwin 1000 --out  1000
pipenv run sttr --meta author,genre,brow,narrative_perspective,year ~/Dropbox/Complexity/Corpora/ --fixwin 5000 --out  5000
pipenv run sttr --meta author,genre,brow,narrative_perspective,year ~/Dropbox/Complexity/Corpora/ --fixwin 10000 --out 10000

cd 1000 && R -f ../visualize.R && mv sttr-plots.pdf 1000-sttr-plots.pdf && cp *sttr-plots.pdf $DISTDIR/ && cd ..
cd 5000 && R -f ../visualize.R && mv sttr-plots.pdf 5000-sttr-plots.pdf && cp *sttr-plots.pdf $DISTDIR/ && cd ..
cd 10000 && R -f ../visualize.R && mv sttr-plots.pdf 10000-sttr-plots.pdf && cp *sttr-plots.pdf $DISTDIR/ && cd ..
