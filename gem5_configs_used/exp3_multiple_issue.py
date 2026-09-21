"""
exp3_multiple_issue.py -- Assignment 4, Part 2, Experiment 3: Multiple
Issue Simulation (X86 build).

Configures gem5's out-of-order X86O3CPU as a superscalar processor and
exposes --issue-width so the SAME benchmark can be run at issue-width 1
(single-issue baseline, comparable to Experiments 1-2) and at a wider
issue-width (e.g. 4) to measure the throughput gained from
multiple-instruction-per-cycle issue.

Every width parameter (fetchWidth, decodeWidth, renameWidth, issueWidth,
wbWidth, commitWidth, numROBEntries) verified directly against this
container's /gem5/src/cpu/o3/BaseO3CPU.py.

Run against each of the three provided benchmarks at both widths, e.g.:
    build/X86/gem5.opt -d m5out_int_w2 configs/assignment4/exp3_multiple_issue.py \\
        --issue-width 2 --binary configs/assignment4/workloads/int_bench_x86
    build/X86/gem5.opt -d m5out_int_w4 configs/assignment4/exp3_multiple_issue.py \\
        --issue-width 4 --binary configs/assignment4/workloads/int_bench_x86
and likewise for fp_bench_x86 and mem_bench_x86.

NOTE (discovered empirically on this checkout): X86O3CPU with
issueWidth=1 hits an internal `TimeBuffer::valid` assertion failure
partway through a compute-heavy SE-mode workload (it works fine for
Experiment 1's trivial "Hello World" binary, but not for a
2-million-iteration loop) -- this is a real limitation of this gem5
version's out-of-order core model at the narrowest width, not a
configuration bug. issue-width=2 is used as the narrow baseline here
instead of 1, and this substitution is documented as such in the
write-up.
"""

import argparse
import os

import m5
from m5.objects import (
    AddrRange,
    X86O3CPU,
    L2XBar,
    MemCtrl,
    Process,
    Root,
    SEWorkload,
    SrcClockDomain,
    System,
    SystemXBar,
    VoltageDomain,
    DDR3_1600_8x8,
)

from common.caches import L1DCache, L1ICache, L2Cache

parser = argparse.ArgumentParser()
parser.add_argument(
    "--issue-width", type=int, default=4,
    help="Instructions issued per cycle (1 = single-issue baseline)",
)
parser.add_argument(
    "--binary", required=True,
    help="Path to the X86 SE-mode benchmark binary to run",
)
args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# ---------------------------------------------------------------------
# CPU: out-of-order X86O3CPU, width scaled by --issue-width
# ---------------------------------------------------------------------
system.cpu = X86O3CPU()
w = args.issue_width
system.cpu.fetchWidth = w
system.cpu.decodeWidth = w
system.cpu.renameWidth = w
system.cpu.issueWidth = w
system.cpu.wbWidth = w
system.cpu.commitWidth = w
system.cpu.numROBEntries = 192

system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

system.l2bus = L2XBar()
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

system.l2cache = L2Cache()
system.l2cache.connectCPUSideBus(system.l2bus)

system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)

system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

binary = os.path.abspath(args.binary)
system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"Experiment 3: issue width = {w} -- beginning simulation of {binary}")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")

