# Assignment 4 -- Instruction-Level Parallelism (ILP)

## What to submit

- `ILP_Literature_Review.docx` -- Part 1: research literature review
  (memory hierarchy discussion included).
- `Part2_Gem5_Practical_Exploration.docx` (and `.pdf`) -- Part 2: the four
  gem5 experiments, with real console-output screenshots, results,
  troubleshooting, and analysis.
- `gem5_configs/` -- the actual gem5 SE-mode config scripts and C
  workload sources used to produce every result in Part 2, included so
  the experiments can be reproduced.

## gem5_configs contents

| File | Purpose |
|---|---|
| `exp1_basic_pipeline.py` | Experiment 1 -- X86O3CPU pinned to width 1 (in-order pipeline stand-in), runs gem5's bundled Hello World binary |
| `exp2_branch_prediction.py` | Experiment 2 -- same width-1 core, `--predictor local\|tournament` |
| `exp3_multiple_issue.py` | Experiment 3 -- superscalar issue-width sweep (`--issue-width`, `--binary`) |
| `exp4_smt.py` | Experiment 4 -- SMT config as originally designed (`m5.simulate()`, unbounded) |
| `exp4_smt_bounded.py` | Same SMT config with `m5.simulate(50_000_000)` -- required because the unbounded version never generates an exit event and never writes `stats.txt` (see Part 2's Troubleshooting section for the full diagnosis: fetch reaches 20 insts/thread, execute/commit stay at 0, reproduced under three independent configurations) |
| `common/caches.py` | Shared L1I/L1D/L2 cache definitions used by all four experiments |
| `workloads/int_bench.c`, `mem_bench.c`, `fp_bench.c` | Full-size C benchmarks used in Experiments 1-3 |
| `workloads/int_bench_smt.c`, `mem_bench_smt.c` | 20x-reduced-iteration variants used as Experiment 4's two SMT threads |

Binaries are not included -- cross-compile for X86 SE mode with:

```bash
x86_64-linux-gnu-gcc -static -no-pie -O1 -o <name>_x86 <name>.c
```

(`-no-pie` is required alongside `-static`; see Part 2's Troubleshooting
section for why plain `-static` alone produces a PIE binary gem5's
SE-mode loader rejects.)

## Running an experiment

```bash
build/X86/gem5.opt -d m5out_exp1 configs/assignment4/exp1_basic_pipeline.py
build/X86/gem5.opt -d m5out_exp2 configs/assignment4/exp2_branch_prediction.py --predictor tournament
build/X86/gem5.opt -d m5out_exp3 configs/assignment4/exp3_multiple_issue.py --issue-width 4 --binary configs/assignment4/workloads/int_bench_x86
build/X86/gem5.opt -d m5out_exp4 configs/assignment4/exp4_smt_bounded.py --binary0 configs/assignment4/workloads/int_bench_smt_x86 --binary1 configs/assignment4/workloads/mem_bench_smt_x86
```

Environment used: gem5 23.0.0.1 (commit af72b9ba5805), X86-only build,
in a Docker container.
