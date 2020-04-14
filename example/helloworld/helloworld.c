#include <stdio.h>

double foo() {
    double sum = 0;
    for (int i = 0; i < 10000000; i++) sum += 1;
    return sum;
}

int
main(void)
{
    printf("hello world!\n");
    double y = foo();
    return 0;
}
