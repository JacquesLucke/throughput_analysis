
import subprocess
from pathlib import Path
from typing import Callable
from dataclasses import dataclass

@dataclass
class ProgramResult:
    throughput: float
    buffer1: int
    buffer2: int

@dataclass
class RecordConfig:
    name: str
    compile_args: list[str]
    sizes: list[str]
    alignment: int = 64
    operation: str = "add"
    iterations_per_size: int = 1
    reduce_throughputs: Callable[[list[float]], float] = lambda x: sum(x) / len(x)

    @property
    def csv_path(self):
        return (results_directory / self.name).with_suffix(".csv")

    @property
    def description(self):
        return f"{' '.join(self.compile_args)}, alignment: {self.alignment}, operation: {self.operation}"

current_directory = Path(__file__).parent
program_path = current_directory / "main"
results_directory = current_directory / "results"

def compile_program(flags: tuple[str] = ()):
    args = [
        "clang++",
        current_directory / "main.cc",
        current_directory / "benchmark_function.cc",
        "-o", current_directory / "main",
        "-std=c++17"
    ]
    args += list(flags)
    print(" ".join([str(arg) for arg in args]))
    subprocess.run(args)

def run_program(args: tuple[str] = ()) -> str:
    args = [program_path] + list(args)
    # print(" ".join([str(arg) for arg in args]))
    output = subprocess.check_output(args).decode("utf8")
    lines = output.splitlines()
    return ProgramResult(
        throughput=float(lines[0]),
        buffer1=int(lines[1], base=16),
        buffer2=int(lines[2], base=16))

def get_alignment(pointer: int) -> int:
    alignment = 1
    while (pointer & alignment) == 0:
        alignment *= 2
    return alignment

def get_offset_in_page(pointer: int) -> int:
    return pointer % 4096

def exponantial_steps(min_size: int, max_size: int, factor: float):
    value = min_size
    while value < max_size:
        yield int(value)
        value = max(value + 1, value * factor)
    yield int(max_size)

def linear_steps(min_size: int, max_size: int, step: int):
    value = min_size
    while value < max_size:
        yield int(value)
        value += step
    yield int(max_size)

def combine_steps(*generators):
    all_steps = set()
    for gen in generators:
        all_steps.update(gen)
    return list(sorted(all_steps))

def record_data(config: RecordConfig):
    compile_program(config.compile_args)
    throughputs = []
    for size in config.sizes:
        runtime_args = (str(size), str(config.alignment), config.operation)
        throughputs_for_size = []
        for _ in range(config.iterations_per_size):
            result = run_program(runtime_args)
            throughputs_for_size.append(result.throughput)
        throughput = config.reduce_throughputs(throughputs_for_size)
        tot_used_bytes = size * 8 # 8 = 2 * sizeof(int)
        print(f"{size:11,}: {throughput:10.3f} iterations/ns    {tot_used_bytes:14,} bytes")
        throughputs.append(throughput)
    return throughputs

def save_as_csv(config: RecordConfig, throughputs: list[float]):
    path = config.csv_path
    with open(path, "w") as f:
        for size, throughput in zip(config.sizes, throughputs):
            f.write(f"{size},{throughput}\n")

def try_load_cached(config: RecordConfig):
    path = config.csv_path
    if not path.exists():
        return None
    with open(path) as f:
        lines = f.readlines()
    sizes = []
    throughputs = []
    for line in lines:
        split = line.split(",")
        sizes.append(int(split[0]))
        throughputs.append(float(split[1]))
    if sizes != config.sizes:
        # Cache is outdated.
        return None
    return throughputs

def get_throughputs_maybe_cached(config: RecordConfig):
    throughputs = try_load_cached(config)
    if throughputs is not None:
        return throughputs
    throughputs = record_data(config)
    save_as_csv(config, throughputs)
    return throughputs

def save_as_plotly_graph(file_name: str, title: str, configs: list[RecordConfig], throughputs_list: list[list[float]], *, log_x: bool = False):
    path = (results_directory / file_name).with_suffix(".html")

    import plotly.graph_objects as go
    fig = go.Figure()
    for config, throughputs in zip(configs, throughputs_list):
        fig.add_trace(go.Scatter(x=config.sizes, y=throughputs, mode="lines", name=config.description))
    if log_x:
        fig.update_xaxes(type="log")
    fig.update_layout(title=title)
    fig.update_xaxes(title="Array Size")
    fig.update_yaxes(title="Iterations per Nanosecond")
    fig.write_html(path, include_plotlyjs="directory")

def generate_figure_for_configs(configs: list[RecordConfig]):
    throughputs_list = []
    for config in configs:
        throughputs = get_throughputs_maybe_cached(config)
        throughputs_list.append(throughputs)
    save_as_plotly_graph("graph_log", "Array Processing Throughput", configs, throughputs_list, log_x=True)
    save_as_plotly_graph("graph_linear", "Array Processing Throughput", configs, throughputs_list, log_x=False)

all_steps = combine_steps(
    linear_steps(1, 200, 1),
    linear_steps(200, 1000, 2),
    linear_steps(1000, 6500, 4),
    linear_steps(6500, 30000, 16),
    exponantial_steps(30000, 100_000_000, 1.01),
)

low_steps = combine_steps(linear_steps(1, 150, 1))

full_optimized_config = RecordConfig(
    name="full_optimized",
    compile_args=("-O3", "-march=native"),
    sizes=all_steps,
)

full_optimized_aligned_config = RecordConfig(
    name="full_optimized_aligned",
    compile_args=("-O3", "-march=native"),
    sizes=all_steps,
    alignment=4096,
)

full_optimized_mul_config = RecordConfig(
    name="full_optimized_mul",
    compile_args=("-O3", "-march=native"),
    sizes=all_steps,
    operation="mul",
)

no_native_optimize_config = RecordConfig(
    name="no_native_optimize",
    compile_args=("-O3", ),
    sizes=all_steps,
)

no_unroll_config = RecordConfig(
    name="no_unroll",
    compile_args=("-O3", "-march=native", "-fno-unroll-loops"),
    sizes=all_steps,
)

no_vectorize_config = RecordConfig(
    name="no_vectorize",
    compile_args=("-O3", "-march=native", "-fno-vectorize"),
    sizes=all_steps,
)

no_vectorize_no_vectorize_config = RecordConfig(
    name="no_unroll_no_vectorize",
    compile_args=("-O3", "-march=native", "-fno-unroll-loops", "-fno-vectorize"),
    sizes=all_steps,
)

generate_figure_for_configs([
    full_optimized_config,
    full_optimized_aligned_config,
    full_optimized_mul_config,
    no_native_optimize_config,
    no_unroll_config,
    no_vectorize_config,
    no_vectorize_no_vectorize_config
])
