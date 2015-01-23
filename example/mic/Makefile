TAUROOT = /home/users/ender/src/tau2/mic_linux

#CC = icc
#CFLAGS = -mmic -vec-report3 -openmp
CC = $(TAUROOT)/bin/tau_cc.sh
CFLAGS = -openmp

export TAU_MAKEFILE = $(TAUROOT)/lib/Makefile.tau-icpc-papi-pthread-pdt

targets = openmp_sample
all: $(targets)

clean:
	rm -f $(targets) *.o
