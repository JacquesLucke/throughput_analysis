#pragma once

void add_operation(const int* in1, int in2, int* result, int size);
void mul_operation(const int* in1, int in2, int* result, int size);

using OperationFn = decltype(&add_operation);
