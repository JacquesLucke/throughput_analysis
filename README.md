# Throughput Analysis

With this repo I tried to get a better intuition for what the maximum possible throughput is when performing a simple operation on an array.

The benchmark is designed so that it is cpu or memory bandwidth bound. That is instead of e.g. memory access latency or branch prediction, which I already investigated in the past:
* https://dev.to/jacqueslucke/a-c-micro-optimization-exercise-3p65
* https://github.com/JacquesLucke/iteration_analysis
* https://github.com/JacquesLucke/cache_latency_analysis

The following aspects are varied between different benchmarks in this project:
* Array size that is processed repeatedly.
* Compiler flags.
* Alignment of the processed arrays.
* Operation that is performed (current only `add` and `multiply` is used).

Some notes:
* `benchmark_functions.cc` contains the functions that are measured.
* `record.py` does the following things:
    * Compiles the c++ code with different compiler flags.
    * Initiates the benchmark for different array sizes.
    * Caches the benchmark results in `.csv` files in the `results` directory.
    * Generates interactive graphs that can be viewed in a webbrowser.
* Even though the benchmarked functions are very simple, the resulting graphs are surprisingly complex. Many performance related aspects of modern CPUs are required to make sense of the results:
    * Different L1, L2 and L3 cache sizes with different bandwidths (see overall structure of the graph).
    * Loop unrolling and vectorization done by the compiler (see 1 - 2k in the graph).
    * Something probably related to page sizes which I can't fully explain yet (see 10k - 30k in the graph).
* The main observations that changed my intuition are the following:
    * Cache bandwidth:
        * The memory bandwidth difference between L2 and L3 cache is measurable but not as significant as I thought when any processing is done on all loaded bytes.
        * An [earlier test](https://github.com/JacquesLucke/cache_latency_analysis/blob/master/cache_latency_L2_L3.png) showed a more significant difference, but it also did much less processing.
        * L1 cache can be quite a bit faster than L2 cache but it only matters when very little processing is done. E.g. when a multiplication is done instead of an addition, the performance difference becomes almost insignificant.
    * Scalar fallback loop:
        * Vectorized and partially unrolled loops process many elements in parallel (32 in my specific case). That also implies that any leftover elements have to be processed in a separate loop. Under some circumstances the majority of the time is spend in the scalar loop (e.g. in the benchmark, processing 95 elements took 3x longer than processing 96 elements).
        * LLVM seems to support [epilogue vectorization](https://llvm.org/docs/Vectorizers.html#epilogue-vectorization) but it didn't seem to have an affect here.
    * Worse performance at regular intervals:
        * Between 10k and 30k in the graph there are regular drops in performance. 
        * I measured them on linux and windows, so it's likely not specific to the allocator.
        * With more alignment, the spikes go away, but overall performance is worse. Also the spikes don't come back when applying an offset in the aligned array. It seems to be related to the total amount of allocated memory.
        * Might also be related to page sizes or cpu cache assoziativity.



![image](results/graph_readme.png)

Note, changes at the 30k mark are most likely caused by a change sampling strategy at that point. Needs further investigation.

Interactive versions of the graph:
* Log X Scale: http://htmlpreview.github.io/?https://github.com/JacquesLucke/throughput_analysis/blob/main/results/graph_log.html
* Linear X Scale: http://htmlpreview.github.io/?https://github.com/JacquesLucke/throughput_analysis/blob/main/results/graph_linear.html

External Dependencies:
* Clang to compile C++17 code.
* Python 3.9+ with plotly.
