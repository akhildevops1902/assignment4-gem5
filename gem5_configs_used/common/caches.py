"""
common/caches.py

Shared L1I / L1D / L2 cache definitions used by all four Assignment 4,
Part 2 experiment scripts. ISA-independent (Cache is a generic gem5
SimObject), so this file is identical for the X86 build.
"""

from m5.objects import Cache


class L1Cache(Cache):
    """Common L1 parameters; each subclass below sets size and wiring."""

    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

    def connectBus(self, bus):
        self.mem_side = bus.cpu_side_ports

    def connectCPU(self, cpu):
        raise NotImplementedError


class L1ICache(L1Cache):
    size = "32KiB"

    def connectCPU(self, cpu):
        self.cpu_side = cpu.icache_port


class L1DCache(L1Cache):
    size = "32KiB"

    def connectCPU(self, cpu):
        self.cpu_side = cpu.dcache_port


class L2Cache(Cache):
    size = "256KiB"
    assoc = 8
    tag_latency = 12
    data_latency = 12
    response_latency = 12
    mshrs = 20
    tgts_per_mshr = 12

    def connectCPUSideBus(self, bus):
        self.cpu_side = bus.mem_side_ports

    def connectMemSideBus(self, bus):
        self.mem_side = bus.cpu_side_ports

