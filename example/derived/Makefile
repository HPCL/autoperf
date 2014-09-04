pi: pi.c
	mpicc -Wall pi.c -o pi

pi_inst: pi.c
	tau_cc.sh -Wall pi.c -o pi_inst

clean:
	rm -f pi pi_inst *.o *~

