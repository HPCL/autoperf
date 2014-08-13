GMP     = /usr/local/packages/gmp/5.0.5
SQLITE3 = $(HOME)/prefix/sqlite-3.8.5

#export TAU_MAKEFILE=$(TAU_ROOT)/x86_64/lib/Makefile.tau-papi-mpi-pdt
#CXX     = tau_cxx.sh

CXX      = g++
CXXFLAGS = -Wall -Wno-write-strings -g -I$(PAPI)/include -I$(GMP)/include -I$(SQLITE3)/include
LDFLAGS  = -L$(PAPI)/lib -L$(GMP)/lib -L$(SQLITE3)/lib -Wl,-rpath=$(SQLITE3)/lib -lpapi -lgmp -lsqlite3

TARGETS = partitioner

all: $(TARGETS)

clean:
	rm -f *.o *~ $(TARGETS)
