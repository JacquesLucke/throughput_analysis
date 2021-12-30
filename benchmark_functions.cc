#include "benchmark_functions.hh"

void add_operation(const int* in1, int in2, int* result, int size) {
  for (int i = 0; i < size; i++) {
    result[i] = in1[i] + in2;
  }
}

void mul_operation(const int* in1, int in2, int* result, int size) {
  for (int i = 0; i < size; i++) {
    result[i] = in1[i] * in2;
  }
}
