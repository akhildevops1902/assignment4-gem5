/* int_bench.c
 * Integer-heavy microbenchmark for the multiple-issue (superscalar)
 * experiment: a long run of independent integer additions and multiplies
 * unrolled by 4 so a wide-issue, out-of-order core has several
 * independent instructions available per cycle to actually exploit.
 */
#include <stdio.h>

#define N 2000000

int main(void) {
    volatile long a = 1, b = 2, c = 3, d = 4;
    for (int i = 0; i < N; i++) {
        a = a * 3 + i;
        b = b * 5 + i;
        c = c * 7 + i;
        d = d * 9 + i;
    }
    printf("int_bench result: %ld\n", a + b + c + d);
    return 0;
}

