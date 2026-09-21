/* mem_bench.c
 * Memory-operation-heavy microbenchmark for the multiple-issue
 * experiment: strided array read-modify-write traffic that keeps the
 * load/store queue and the L1D/L2 hierarchy busy instead of executing
 * on data already resident in registers.
 */
#include <stdio.h>
#include <stdlib.h>

#define SIZE 65536
#define ITERS 200

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

