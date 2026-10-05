#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "startup")) { puts("startup"); return 0; }
    int *a = calloc(4096, sizeof(*a));
    if (!a) return 3;
#pragma omp parallel for schedule(dynamic,64) num_threads(4)
    for (int i = 0; i < 4096; ++i) a[i] = i;
    long long sum = 0;
    for (int i = 0; i < 4096; ++i) sum += a[i];
    if (sum != 4095LL * 4096 / 2) return 4;
    if (!strcmp(argv[1], "race")) {
        volatile int shared = 0;
#pragma omp parallel for schedule(dynamic,64) num_threads(4)
        for (int i = 0; i < 4096; ++i) shared += i & 1;
        printf("racy=%d\n", shared);
    } else if (strcmp(argv[1], "clean")) return 5;
    free(a);
    return 0;
}
