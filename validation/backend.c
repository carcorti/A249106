/* Test-only translation unit. The production source has one canonical build. */
#define A249106_FORCE_FALLBACK 1
#define main a249106_embedded_main
#include "../src/a249106.c"
#undef main

int main(void) {
    if (isqrt64(UINT64_MAX) != UINT64_C(4294967295))
        die("isqrt64 maximal value");
    if (isqrt64(UINT64_C(18446744065119617025)) != UINT64_C(4294967295))
        die("isqrt64 maximal square");
    if (!prime64(UINT64_C(2305843009213693951)) ||
        prime64(UINT64_MAX))
        die("deterministic 64-bit primality");
    bool fb=false;
    uint64_t n=UINT64_C(1009)*UINT64_C(1013);
    uint64_t d=split64(n,&fb);
    if (!fb || d!=1009) die("forced exact fallback");
    u128 value=0;
    if (!derivative64(n,&value,&fb) ||
        value!=(u128)1009+1013) die("factor derivative");
    u128 u=CAP;
    const u128 expected[4]={
        (u128)22050000000000000ULL,
        (u128)595350000000000000ULL,
        (u128)17562825000000000000ULL,
        (u128)5532289875000000000ULL*100
    };
    for(unsigned j=0;j<4;++j) {
        unsigned bits=0; u128 z=u;
        while(z) { ++bits; z>>=1; }
        u=u*(bits-1)/2;
        if(u!=expected[j]) die("capacity envelope mismatch");
    }
    if(expected[2]>UINT64_MAX)
        die("capacity width");
    fb=false;
    if(!derivative64(UINT64_MAX,&value,&fb) ||
       value!=(u128)11024205608477874323ULL)
        die("64-bit maximal operand derivative");
    fb=false;
    if(!derivative64((uint64_t)expected[2],&value,&fb) ||
       value!=(u128)1891398600000000000ULL*100 ||
       value<=UINT64_MAX)
        die("wide fourth derivative boundary");
    mpz_t z,q,r;
    mpz_inits(z,q,r,NULL);
    u128 wide_root=((u128)1<<64)+12345;
    mpz_set128(z,wide_root);
    mpz_mul(q,z,z);
    if(!mpz_perfect_square_p(q)) die("wide GMP square");
    mpz_sqrt(r,q);
    u128 recovered=0;
    if(!mpz_get128_checked(r,&recovered)||recovered!=wide_root)
        die("wide GMP root round trip");
    mpz_clears(z,q,r,NULL);
    Hit h; fb=false;
    if(predicate(19164,25564,&h,&fb)!=1 || h.root!=96336 ||
       h.x2!=31848 || h.x3!=58412 || h.x4!=61916)
        die("known positive chain");
    puts("BACKEND PASS");
    return 0;
}
