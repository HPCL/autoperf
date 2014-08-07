TARGETS = mpi_pi mpi_pi_pdt

export TAU_MAKEFILE = $(TAU_ROOT)/x86_64/lib/Makefile.tau-papi-mpi-pdt

all: $(TARGETS)

mpi_pi:
	mpicc -Wall mpi_pi.c -o mpi_pi

mpi_pi_pdt:
	tau_cc.sh -Wall mpi_pi.c -o mpi_pi_pdt

clean:
	rm -f *.o $(TARGETS) *~

