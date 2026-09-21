/* mem_bench_smt.c
 * Smaller variant of mem_bench.c used only for Experiment 4 (SMT),
 * where simulating two full-size benchmarks concurrently in detailed
 * SMT timing mode proved pathologically slow on this gem5 version.
 * Same access pattern, 20x fewer outer iterations.
 */
#include <stdio.h>
#include <stdlib.h>

#define SIZE 65536
#define ITERS 10

int main(void) {
    static int arr[SIZE];
    for (int i = 0; i < SIZE; i++) arr[i] = i;

    long total = 0;
    for (int it = 0; it < ITERS; it++) {
        for (int i = 0; i < SIZE; i += 8) {
            arr[i] = arr[i] + arr[(i + 37) % SIZE];
            total += arr[i];
        }
    }
    printf("mem_bench result: %ld\n", total);
    return 0;
}
