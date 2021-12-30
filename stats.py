'''
requires: plotly, pandas
'''

import subprocess
from pathlib import Path
import plotly.express
from dataclasses import dataclass

@dataclass
class ProgramResult:
    throughput: float
    buffer1: int
    buffer2: int

current_directory = Path(__file__).parent
program_path = current_directory / "main"

def compile_program(flags: tuple[str] = ()):
    args = [
        "clang++",
        current_directory / "main.cc",
        current_directory / "function.cc",
        "-o", current_directory / "main",
        "-std=c++17"
    ]
    args += list(flags)
    print("Run", " ".join([str(arg) for arg in args]))
    subprocess.run(args)

def run_program(args: tuple[str] = ()) -> str:
    args = [program_path] + list(args)
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


def generate_exponential_sizes(min_size: int, max_size: int, factor: float):
    value = min_size
    while value < max_size:
        yield int(value)
        value = max(value + 1, value * factor)
    yield int(max_size)

def generate_linear_sizes(min_size: int, max_size: int, step: int):
    value = min_size
    while value < max_size:
        yield int(value)
        value += step
    yield int(max_size)

def generate_sizes():
    # yield from generate_linear_sizes(1, 100, 1)
    yield from generate_linear_sizes(5000, 8000, 16)

sizes = []
throughputs = []

compile_program(("-O3", "-march=native"))
# for size in generate_exponential_sizes(490000, 500000, 1.0001):
for size in generate_sizes():
    args = (str(size), )
    tot_used_bytes = size * 8 # 8 = 2 * sizeof(int)
    iterations = 3
    throughputs_for_size = []
    for _ in range(iterations):
        result = run_program(args)
        single_throughput = result.throughput
        # print(result.buffer1, get_alignment(result.buffer1), get_offset_in_page(result.buffer1))
        # print(get_alignment(result.buffer2), get_offset_in_page(result.buffer2))
        throughputs_for_size.append(single_throughput)
    throughput = list(sorted(throughputs_for_size))[1] 
    print(f"{size:11,}: {throughput:10.3f} iterations/ns    {tot_used_bytes:14,} bytes")
    sizes.append(size)
    throughputs.append(throughput)

figure = plotly.express.line(x=sizes, y=throughputs, log_x=False)
figure.show()
