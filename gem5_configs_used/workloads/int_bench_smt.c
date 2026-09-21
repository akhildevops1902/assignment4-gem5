/* int_bench_smt.c
 * Smaller variant of int_bench.c used only for Experiment 4 (SMT),
 * where simulating two full-size benchmarks concurrently in detailed
 * SMT timing mode proved pathologically slow on this gem5 version.
 * Same instruction mix, 20x fewer iterations.
 */
#include <stdio.h>

#define N 100000

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
