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

template <typename T> T *alloc_buffer(const int64_t size) {
  const int64_t offset = 0;
  const int64_t tot_size = sizeof(T) * size + 0;
  char *original_buffer = (char *)aligned_alloc(64, tot_size);

  /* Read and write to each element once. */
  memset(original_buffer, 0, tot_size);
  for (int64_t i = 0; i < tot_size; i++) {
    original_buffer[i] = original_buffer[tot_size - i - 1];
  }

  return reinterpret_cast<T *>(original_buffer + offset);
}

int main(int argc, char const *argv[]) {

  argparse::ArgumentParser arg_parser("throughput_analysis");
  arg_parser.add_argument("buffer_size")
      .help("size of the buffer used in each iteration")
      .scan<'i', int64_t>()
      .default_value<int64_t>(1e5);
  try {
    arg_parser.parse_args(argc, argv);
  } catch (const std::runtime_error &err) {
    std::cerr << err.what() << "\n";
    std::cerr << arg_parser;
    return 1;
  }

  const int64_t tot_throughput = 1e9;

  const int64_t buffer_size = arg_parser.get<int64_t>("buffer_size");
  int *buffer1 = alloc_buffer<int>(buffer_size);
  int *buffer2 = alloc_buffer<int>(buffer_size);
  const int64_t value = 1;

  const int64_t iterations = tot_throughput / buffer_size;

  const auto start_time = std::chrono::high_resolution_clock::now();
  {
    for (int64_t iter = 0; iter < iterations; iter++) {
      add_constant(buffer1, value, buffer2, buffer_size);
      // std::swap(a, b);
    }
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
