#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>

#include "external/argparse/argparse.hpp"

#include "function.hh"

/**
 * Variables to change:
 * - offset in page
 * - operation complexity
 */

static void* aligned_allocate(const int64_t size, const int64_t alignment) {
  void* buffer = malloc(size + alignment - 1);
  return (void*)(((uintptr_t)buffer + alignment) & ~(uintptr_t)(alignment - 1));
}

template <typename T>
static T* alloc_buffer(const int64_t size, const int64_t alignment) {
  const int64_t offset = 0;
  const int64_t tot_size = sizeof(T) * size + offset;
  char* original_buffer = (char*)aligned_allocate(tot_size, alignment);
  return reinterpret_cast<T*>(original_buffer + offset);
}

int main(int argc, char const* argv[]) {
  argparse::ArgumentParser arg_parser("throughput_analysis");
  arg_parser.add_argument("buffer_size")
      .help("size of the buffer used in each iteration")
      .scan<'i', int64_t>()
      .default_value<int64_t>(1e5);
  arg_parser.add_argument("alignment")
      .help("alignment of the buffers being processed")
      .scan<'i', int64_t>()
      .default_value<int64_t>(64);
  arg_parser.add_argument("operation")
      .default_value<std::string>("add")
      .help("'add' or 'mul'");

  try {
    arg_parser.parse_args(argc, argv);
  } catch (const std::runtime_error& err) {
    std::cerr << err.what() << "\n";
    std::cerr << arg_parser;
    return 1;
  }

  const int64_t tot_throughput = 1e9;

  const int64_t buffer_size = arg_parser.get<int64_t>("buffer_size");
  const int64_t alignment = arg_parser.get<int64_t>("alignment");
  int* buffer1 = alloc_buffer<int>(buffer_size, alignment);
  int* buffer2 = alloc_buffer<int>(buffer_size, alignment);

  const std::string operation_name = arg_parser.get<std::string>("operation");
  OperationFn operation_fn = add_operation;
  if (operation_name == "mul") {
    operation_fn = mul_operation;
  }

  const int64_t iterations = tot_throughput / buffer_size;

  /* Warm up memory. */
  operation_fn(buffer1, 42, buffer2, buffer_size);

  const auto start_time = std::chrono::high_resolution_clock::now();
  for (int64_t iter = 0; iter < iterations; iter++) {
    operation_fn(buffer1, 42, buffer2, buffer_size);
  }
  const auto end_time = std::chrono::high_resolution_clock::now();

  const std::chrono::nanoseconds duration = end_time - start_time;
  const double duration_ms = duration.count() / 1'000'000.0;
  const int64_t throughput_ms = buffer_size * iterations / duration_ms;
  const double throughput_ns = throughput_ms / 1'000'000.0;
  // std::cout << "Time: " << duration_ms << " ms\n";
  // std::cout << "Throughput: " << throughput_ns << " iterations/ns\n";
  std::cout << throughput_ns << "\n";
  std::cout << buffer1 << "\n";
  std::cout << buffer2 << "\n";

  return 0;
}
