# PAPI and CUDA variables are assumed in the environment

#export TAU_MAKEFILE=$(TAU_ROOT)/x86_64/lib/Makefile.tau-papi-mpi-pdt
#CXX     = tau_cxx.sh

CC       = gcc
CXX      = g++
CPPFLAGS = -I$(PAPI)/include
CXXFLAGS = -Wall -Wno-write-strings -g
LDFLAGS  = -L$(PAPI)/lib -Wl,-rpath=$(PAPI)/lib -lpthread -ldl
LDLIBS   = -lpapi 

ifdef CUDA
CPPFLAGS += -DWITH_CUPTI -I$(CUDA)/include -I$(CUDA)/extras/CUPTI/include
LDFLAGS  += -L$(CUDA)/lib64 -L$(CUDA)/extras/CUPTI/lib64
LDLIBS   += -lcuda -lcudart -lcupti
endif

TARGETS = partitioner libgprof-helper.so

PAPI_METRICS = PAPI_FP_INS PAPI_TOT_INS PAPI_RES_STL PAPI_TOT_CYC \
               PAPI_L1_DCM PAPI_L1_ICM PAPI_L2_DCM PAPI_L2_ICM    \
               PAPI_L1_TCM PAPI_L2_TCM PAPI_L3_TCM

CUDA_METRICS = CUDA.Tesla_K20c.domain_a.tex0_cache_sector_queries \
               CUDA.Tesla_K20c.domain_a.tex1_cache_sector_queries \
               CUDA.Tesla_K20c.domain_a.tex2_cache_sector_queries \
               CUDA.Tesla_K20c.domain_a.tex3_cache_sector_queries \
               CUDA.Tesla_K20c.domain_a.tex0_cache_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp0_write_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp1_write_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp2_write_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp3_write_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp0_read_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp1_read_sector_misses \
               CUDA.Tesla_K20c.domain_b.l2_subp2_read_sector_misses

MISC_METRICS = TIME

METRICS = $(PAPI_METRICS) $(CUDA_METRICS) $(MISC_METRICS)

all: $(TARGETS)

partitioner: sqlite3.o partitioner.o
	$(CXX) -o $@ $^ $(LDFLAGS) $(LDLIBS) 

partitioner.o: partitioner.cpp
	$(CXX) -c $^ $(CPPFLAGS) $(CXXFLAGS) 

sqlite3.o: sqlite3.c
	$(CC) -c sqlite3.c 

libgprof-helper.so: gprof-helper.c
	$(CC) -shared -fPIC $< -o $@ -lpthread -ldl

test:
	./partitioner sqlite3.db $(subst $(eval) ,:,$(METRICS)) greedy true

clean:
	rm -f *.o *~ $(TARGETS)
