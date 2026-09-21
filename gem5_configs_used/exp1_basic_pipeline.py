"""
exp1_basic_pipeline.py -- Assignment 4, Part 2, Experiment 1: Basic
Pipeline Simulation (X86 build).

Rewritten for this gem5 checkout (commit af72b9ba5805, 2023-07-10,
X86-only build): gem5's MinorCPU.py only aliases to ArmMinorCPU /
RiscvMinorCPU, so there is no in-order MinorCPU model for X86. The
substitute used here, and stated as such in the write-up, is X86O3CPU
(the out-of-order superscalar core) with every width parameter pinned
to 1: an out-of-order core that can only fetch/decode/rename/issue/
commit one instruction per cycle behaves as a single-issue pipeline for
throughput purposes, which is what this experiment needs.

All parameter names verified directly against this container's
/gem5/src/cpu/o3/BaseO3CPU.py: fetchWidth, decodeWidth, renameWidth,
issueWidth, wbWidth, commitWidth. X86 interrupt wiring verified against
/gem5/configs/learning_gem5/part1/two_level.py (X86 needs explicit
pio/int_requestor/int_responder port connections; ARM's single-call
createInterruptController() is not sufficient on X86).

Workload: gem5's own bundled X86 "Hello World" SE-mode binary
(tests/test-progs/hello/bin/x86/linux/hello).

Run from the gem5 root directory:
    build/X86/gem5.opt configs/assignment4/exp1_basic_pipeline.py
"""

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

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

# ---------------------------------------------------------------------
# CPU: X86O3CPU narrowed to width=1 everywhere -- substitute for a
# single-issue, in-order 5-stage pipeline (no X86 MinorCPU exists).
# ---------------------------------------------------------------------
system.cpu = X86O3CPU()
system.cpu.fetchWidth = 1
system.cpu.decodeWidth = 1
system.cpu.renameWidth = 1
system.cpu.issueWidth = 1
system.cpu.wbWidth = 1
system.cpu.commitWidth = 1
system.cpu.numROBEntries = 32

# ---------------------------------------------------------------------
# Two-level cache hierarchy (memory stage)
# ---------------------------------------------------------------------
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

# X86 requires explicit interrupt-controller port wiring (unlike ARM's
# single-call createInterruptController()).
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

# ---------------------------------------------------------------------
# Workload
# ---------------------------------------------------------------------
thispath = os.path.dirname(os.path.realpath(__file__))
binary = os.path.join(
    thispath, "..", "..", "tests", "test-progs", "hello", "bin",
    "x86", "linux", "hello",
)

system.workload = SEWorkload.init_compatible(binary)
process = Process()
process.cmd = [binary]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Experiment 1: basic single-issue pipeline (X86O3CPU, width=1) -- beginning simulation")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")

