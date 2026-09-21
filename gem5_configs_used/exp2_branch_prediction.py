"""
exp2_branch_prediction.py -- Assignment 4, Part 2, Experiment 2: Impact
of Branch Prediction (X86 build).

Same width=1 X86O3CPU base as Experiment 1, with a selectable
conditional branch predictor so the same workload can be run twice --
once with a minimal predictor, once with a stronger one -- and the
resulting throughput/misprediction stats compared.

Real gem5 API note for THIS checkout (verified directly against
/gem5/src/cpu/pred/BranchPredictor.py in the user's container -- this
is an older gem5 version than the bleeding-edge API): LocalBP and
TournamentBP are direct subclasses of BranchPredictor and are assigned
straight to cpu.branchPred, with NO wrapper class:
    system.cpu.branchPred = LocalBP()
There is no `BranchPredictor(conditionalBranchPred=...)` wrapper in
this gem5 version -- that is a newer-gem5-only API and would fail here.

  --predictor local       LocalBP: a single-level, per-address 2-bit
                           predictor -- the simplest dynamic predictor
                           gem5 ships, standing in for the assignment's
                           "simple/basic" predictor.
  --predictor tournament   TournamentBP: a 2-level adaptive predictor
                           that chooses per-branch between a local and a
                           global history predictor -- substantially
                           more accurate.

Run each configuration from the gem5 root and diff the two m5out
stats.txt files:
    build/X86/gem5.opt -d m5out_local \\
        configs/assignment4/exp2_branch_prediction.py --predictor local
    build/X86/gem5.opt -d m5out_tournament \\
        configs/assignment4/exp2_branch_prediction.py --predictor tournament
"""

import argparse
import os

import m5
from m5.objects import (
    AddrRange,
    X86O3CPU,
    L2XBar,
    LocalBP,
    MemCtrl,
    Process,
    Root,
    SEWorkload,
    SrcClockDomain,
    System,
    SystemXBar,
    TournamentBP,
    VoltageDomain,
    DDR3_1600_8x8,
)

from common.caches import L1DCache, L1ICache, L2Cache

parser = argparse.ArgumentParser()
parser.add_argument(
    "--predictor", choices=["local", "tournament"], default="tournament",
    help="Conditional branch predictor to use (default: tournament)",
)
parser.add_argument(
    "--binary", default=None,
    help="Path to an SE-mode X86 binary to run (default: bundled hello)",
)
args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

system.cpu = X86O3CPU()
system.cpu.fetchWidth = 1
system.cpu.decodeWidth = 1
system.cpu.renameWidth = 1
system.cpu.issueWidth = 1
system.cpu.wbWidth = 1
system.cpu.commitWidth = 1
system.cpu.numROBEntries = 32

# ---------------------------------------------------------------------
# Selectable conditional branch predictor -- direct assignment, no
# wrapper class, per this gem5 version's BranchPredictor.py hierarchy.
# ---------------------------------------------------------------------
if args.predictor == "local":
    system.cpu.branchPred = LocalBP()
else:
    system.cpu.branchPred = TournamentBP()

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

thispath = os.path.dirname(os.path.realpath(__file__))
binary = args.binary or os.path.join(
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

print(f"Experiment 2: branch prediction = {args.predictor} -- beginning simulation")
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")

