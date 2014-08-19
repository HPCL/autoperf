#!/bin/sh

pprof -f {insname}/MULTI__TIME/profile -d >.dump.$$
tau_reduce -f .dump.$$ > {selfile}
rm -f .dump.$$
