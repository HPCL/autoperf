#include "mpi.h" 
#include <stdio.h> 
#include <math.h>
#include <stdlib.h>

int main( int argc, char *argv[] ) 
{
    long n;
    int myid, numproc, i; 
    double PI25DT = 3.141592653589793238462643; 
    double mypi, pi, h, sum, x;
    double begin, end;

    MPI_Init(&argc, &argv); 
    MPI_Comm_size(MPI_COMM_WORLD, &numproc); 
    MPI_Comm_rank(MPI_COMM_WORLD, &myid);

    if (myid == 0) { 
	begin = MPI_Wtime();
    } 

    n = atoi(argv[1]);
    if (n == 0) {
	return 0;
    } else { 
	h   = 1.0 / (double) n; 
	sum = 0.0; 
	for (i = myid + 1; i <= n; i += numproc) { 
	    x = h * ((double)i - 0.5); 
	    sum += (4.0 / (1.0 + x*x)); 
	} 
	mypi = h * sum; 
	MPI_Reduce(&mypi, &pi, 1, MPI_DOUBLE, MPI_SUM, 0, 
		   MPI_COMM_WORLD); 
	if (myid == 0)  
	    printf("pi is approximately %.16f, Error is %.16f\n", 
		   pi, fabs(pi - PI25DT)); 
    } 

    if (myid == 0) {
	end = MPI_Wtime();
	printf("time: %f\n", end - begin);
    }
    
    MPI_Finalize();
    return 0; 
}
