/* fp_bench.c
 * Floating-point-heavy microbenchmark for the multiple-issue experiment:
 * four independent accumulators so the FP functional units can be kept
 * busy in parallel rather than waiting on a single dependency chain.
 */
#include <stdio.h>

#define N 2000000

int main(void) {
    volatile double a = 1.0, b = 2.0, c = 3.0, d = 4.0;
    for (int i = 0; i < N; i++) {
        a = a * 1.0001 + 0.5;
        b = b * 1.0002 + 0.5;
        c = c * 1.0003 + 0.5;
        d = d * 1.0004 + 0.5;
    }
    printf("fp_bench result: %f\n", a + b + c + d);
    return 0;
}

