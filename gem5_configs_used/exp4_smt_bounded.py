"""
exp4_smt.py -- Assignment 4, Part 2, Experiment 4: Multithreading (SMT)
(X86 build).

Configures the same X86O3CPU superscalar core from Experiment 3 with
Simultaneous Multithreading enabled: numThreads=2 and two independent
SE-mode processes assigned as two hardware thread contexts sharing one
physical pipeline, reorder buffer, issue queues, and load/store queue.

Real gem5 API note, verified against this container's
src/cpu/o3/BaseO3CPU.py and src/cpu/BaseCPU.py: `numThreads` is a plain
BaseCPU parameter, and a CPU's `workload` parameter is a
VectorParam.Process -- assigning it a Python list of two Process
objects (rather than one) is how gem5 SE mode gives a multi-threaded
CPU model more than one hardware thread context to schedule.

SMT policy parameters confirmed present in this checkout: smtFetchPolicy,
smtROBPolicy, smtROBThreshold, smtLSQPolicy, smtLSQThreshold. This
script defaults ROB/LSQ partitioning to "Threshold" at a 60% cap per
thread so neither thread can starve the other -- vary --rob-share to
see the contention/bottleneck trade-off the assignment asks about.

Run two copies of a benchmark as the two SMT threads, e.g.:
    build/X86/gem5.opt configs/assignment4/exp4_smt.py \\
        --binary0 configs/assignment4/workloads/int_bench_x86 \\
        --binary1 configs/assignment4/workloads/mem_bench_x86
Compare system.cpu.ipc and per-thread committed-instruction counts in
stats.txt against a single-thread run of exp3_multiple_issue.py at the
same issue width.
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
parser.add_argument("--issue-width", type=int, default=4)
parser.add_argument(
    "--rob-share", type=int, default=60,
    help="Per-thread ROB/LSQ threshold percentage under Threshold "
         "partitioning (default: 60)",
)
parser.add_argument("--binary0", required=True, help="Thread 0 SE binary")
parser.add_argument("--binary1", required=True, help="Thread 1 SE binary")
args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# A System must explicitly opt into multi-threaded CPUs -- without this,
# a CPU with numThreads > 1 fails registerThreadContexts() with:
# "Assertion `system->multiThread || numThreads == 1' failed."
# Verified against this checkout's src/sim/system.cc:169
# ("multiThread(p.multi_thread)") -- the Python-side param is the
# snake_case `multi_thread`, not `multiThread`.
system.multi_thread = True

# ---------------------------------------------------------------------
# CPU: superscalar X86O3CPU with two SMT hardware thread contexts
# ---------------------------------------------------------------------
system.cpu = X86O3CPU()
system.cpu.numThreads = 2

w = args.issue_width
system.cpu.fetchWidth = w
system.cpu.decodeWidth = w
system.cpu.renameWidth = w
system.cpu.issueWidth = w
system.cpu.wbWidth = w
system.cpu.commitWidth = w
system.cpu.numROBEntries = max(64, w * 48)

# SMT resource-sharing policy: Threshold partitioning caps each thread's
# share of the ROB and LSQ so one thread cannot starve the other.
system.cpu.smtFetchPolicy = "RoundRobin"
system.cpu.smtROBPolicy = "Threshold"
system.cpu.smtROBThreshold = args.rob_share
system.cpu.smtLSQPolicy = "Threshold"
system.cpu.smtLSQThreshold = args.rob_share

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

# With numThreads=2, createInterruptController() creates one interrupt
# controller PER THREAD (interrupts[0] and interrupts[1]) -- wiring only
# interrupts[0] leaves interrupts[1]'s ports unconnected, which panics
# at m5.instantiate() with "Int port not connected to anything!"
# (found empirically on this checkout). Wire every thread's controller.
system.cpu.createInterruptController()
for i in range(system.cpu.numThreads):
    system.cpu.interrupts[i].pio = system.membus.mem_side_ports
    system.cpu.interrupts[i].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[i].int_responder = system.membus.mem_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

# ---------------------------------------------------------------------
# Two independent SE-mode processes, one per hardware thread context
# ---------------------------------------------------------------------
binary0 = os.path.abspath(args.binary0)
binary1 = os.path.abspath(args.binary1)

system.workload = SEWorkload.init_compatible(binary0)

process0 = Process(pid=100)
process0.cmd = [binary0]
process1 = Process(pid=101)
process1.cmd = [binary1]

system.cpu.workload = [process0, process1]
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(
    f"Experiment 4: SMT with 2 threads, issue width {w} -- "
    f"thread0={binary0}, thread1={binary1}"
)
exit_event = m5.simulate(50_000_000)  # bounded: unbounded run never exits (see Troubleshooting)
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
