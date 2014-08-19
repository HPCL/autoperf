TARGETS = mpi_pi mpi_pi_pdt mpi_pi_sel

all: $(TARGETS)

mpi_pi:
	mpicc -Wall mpi_pi.c -o mpi_pi

mpi_pi_pdt:
	tau_cc.sh -Wall mpi_pi.c -o mpi_pi_pdt

mpi_pi_sel:
	tau_cc.sh -Wall mpi_pi.c -o mpi_pi_sel

clean:
	rm -f *.o $(TARGETS) *~

