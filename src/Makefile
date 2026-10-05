CC = gcc
CFLAGS = -O3 -std=c17 -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wdouble-promotion -Wformat=2 -Werror -fopenmp
CPPFLAGS ?=
LDFLAGS ?= -fopenmp
LDLIBS ?= -lgmp -lcrypto

.PHONY: all clean
all: a249106

a249106: a249106.c Makefile
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ a249106.c $(LDFLAGS) $(LDLIBS)

clean:
	rm -f a249106
