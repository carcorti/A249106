/* Test-only fault injector; never linked into the production executable. */
#define _GNU_SOURCE
#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

struct dirent *readdir(DIR *dir) {
    static struct dirent *(*real_call)(DIR *);
    static unsigned seen;
    if (!real_call) {
        void *sym=dlsym(RTLD_NEXT,"readdir");
        _Static_assert(sizeof sym==sizeof real_call,"test host pointer sizes");
        memcpy(&real_call,&sym,sizeof sym);
        if (!real_call) _exit(99);
    }
    struct dirent *entry=real_call(dir);
    const char *which=getenv("A249106_TEST_READDIR_AT");
    if (entry && which && !strcmp(entry->d_name,"s000000000a.tsv") &&
        ++seen==(unsigned)strtoul(which,NULL,10)) {
        const char *kind=getenv("A249106_TEST_READDIR_KIND");
        if (kind && !strcmp(kind,"signal")) raise(SIGINT);
        fputs("INJECT readdir error\n",stderr);
        errno=kind && strcmp(kind,"eio") ? EINTR : EIO;
        return NULL;
    }
    return entry;
}
int fsync(int fd) {
    static int (*real_call)(int);
    if (!real_call) {
        void *sym=dlsym(RTLD_NEXT,"fsync");
        _Static_assert(sizeof sym==sizeof real_call,"test host pointer sizes");
        memcpy(&real_call,&sym,sizeof sym);
        if (!real_call) _exit(99);
    }
    const char *parent=getenv("A249106_TEST_PARENT");
    if (parent) {
        struct stat st;
        if (!fstat(fd,&st) && S_ISDIR(st.st_mode)) {
            char link[64],path[4096];
            snprintf(link,sizeof link,"/proc/self/fd/%d",fd);
            ssize_t n=readlink(link,path,sizeof path-1);
            if(n<0) _exit(98);
            path[n]=0;
            fprintf(stderr,"SYNC %s\n",path);
            if (!strcmp(path,parent) && getenv("A249106_TEST_PARENT_FAIL")) {
                errno=EIO;
                return -1;
            }
        }
    }
    return real_call(fd);
}
