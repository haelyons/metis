#!/usr/bin/env python3
"""Runner for measure run m2: a one-thread GPU Thomas solve against a parallel cyclic reduction solve.

What it measures. One rented GPU box times two hand-written CUDA solvers of a tridiagonal linear system.
A tridiagonal matrix has nonzeros only on its main diagonal and the two diagonals next to it.
The first solver is the Thomas algorithm (forward elimination, then back substitution) on one CUDA thread.
The second is parallel cyclic reduction (PCR): one thread per equation per round, log2(N) rounds.
Systems have N equations, N in 2^10, 2^14, 2^18, 2^22, 2^24, with five seeds each.
Two independent references check the answers first: NVIDIA cuSPARSE gtsv2_nopivot and scipy solve_banded.
The card's own decision rule is then read from the timings.

Stages, in the order onbox_m2.sh runs them. Each stage reads only files that earlier stages wrote.
So each stage can be run again on its own.
  build             check numpy, scipy.linalg and nvcc; write the CUDA source; compile it; record labels
  gpucheck          cudaGetDeviceCount >= 1 through ctypes
  anchor            planted arithmetic controls (I2..I10, gate propagation); readout control (I1); anchor (E1, E2)
  timers            CPU sleep clock; cudaEvent against the wall clock; a block of 2R solves against R
  residual_sweep    one Thomas and one PCR solve per level and seed, residuals recorded (report only)
  thomas_gpu pcr_gpu cusparse_gpu thomas_batched_gpu launch_probe cpu_dgtsv      the timing arms
  endpoints         E3..E10 from the timing rows
  summary           m2_summary.json: restates the records and decides nothing
  guard             time and cost guard arithmetic, used by onbox_m2.sh before every stage
The pipeline template's stage names map onto these groups.
extract = build + gpucheck; generate = anchor through cpu_dgtsv; endpoints = endpoints.

  python3 run_m2.py --selftest      stdlib only: no numpy, no scipy, no CUDA
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import glob
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "m2"

# ------------------------------------------------------------------------------------------------------------
# Fixed numbers. Each comes from the design record or the execution note. GUESS marks the design's guesses.
# ------------------------------------------------------------------------------------------------------------
LEVELS = [2 ** 10, 2 ** 14, 2 ** 18, 2 ** 22, 2 ** 24]   # sweep levels, the card's compute axis
SEEDS = [0, 1, 2, 3, 4]                                   # one generated system per seed
ANCHOR_LEVELS = [2 ** 10, 2 ** 14]
ANCHOR_SEED = 0
WARMUPS = 2                                               # warm-up solves before each timed block
BLOCK_MS = 50.0                                           # GUESS: R = max(1, ceil(50 ms / warm-up ms per solve))
K_CAP, K_TOTAL = 256, 2 ** 28                             # GUESS: batched copies K = min(256, 2^28 / N)
PCR_BLOCKDIM = 256
B_DIAG = 3.0                                              # diagonal value; off-diagonals are signs of size 1
RES_TOL = 1e-10                                           # the card's residual tolerance
DIFF_TOL = 1e-8                                           # the card's agreement tolerance (checks 1 to 4)
E2_GUESS, E2_BAND = 1e-13, (1e-14, 1e-12)
GATE_SPEEDUP = 2.0
E5_PROXY, E5_BAND = 28.0, (9.3, 84.0)
E6_LOG_MAX, E6_LIN_MIN = 1.15, 1.7                        # GUESS thresholds for the growth shape
E8_BAND = (0.9, 3.0)
E10_BAND = (0.67, 6.0)
E10_NEED_H = 2.0
LAUNCH_BOUND = 0.5
I1_EXACT_TOL, I1_PERTURB, I1_BAND = 1e-14, 1e-6, (1e-7, 1e-5)
TIMER_N = 2 ** 14
TIMER_SLEEP_MS, TIMER_SLEEP_TOL_MS = 100.0, 5.0
TIMER_EVENT_TOL, TIMER_2R_TOL = 0.05, 0.15

# Guard constants. They bound spend and wall-clock only; they decide nothing about the card.
GUARD_RESERVE_S = 90        # kept free at the end for the summary and the done marker
GUARD_TEARDOWN_S = 300      # billed time after the done marker: launcher poll, fetch, terminate
GUARD_MIN_STAGE_S = 30      # a stage is not started with less time than this

LABEL_DRAMATURG = "card dramaturg: REJECT (3 blocking, citations)"
LABEL_BASELINE = "baseline: one CUDA thread per system, this build's kernel"
LABEL_ANCHOR_FAILED = "descriptive only; anchor failed"
LABEL_ONE_REF = "one reference only"
ROLE_REPORT_ONLY = "report-only; does not decide the card"
SUMMARY_NOTE = ("Restates the records under records/ and decides nothing. The five seeds are five different "
                "generated systems timed on one box, not separate boxes.")

# Execution note item 2: an anchor failure labels that solver's rows and leaves the card unread.
# Only disagreeing references (and the other gates) make run_valid false. Set True to void on anchor failure.
ANCHOR_FAIL_VOIDS_RUN = False

EXIT_OK, EXIT_ERROR, EXIT_TOOLCHAIN, EXIT_GPU, EXIT_ENV, EXIT_GUARD_STOP, EXIT_WRONG_VARIANCE = 0, 1, 2, 3, 4, 5, 6
SPARSE_BASE = 100000        # status codes at or above this are cuSPARSE statuses plus this base

TIMING_ARMS = ["thomas_gpu", "pcr_gpu", "cusparse_gpu", "thomas_batched_gpu", "launch_probe", "cpu_dgtsv"]
SWEEP_ROW_FILES = ["residual_sweep"] + TIMING_ARMS
ARM_SOLVER = {"thomas_gpu": "thomas", "thomas_batched_gpu": "thomas", "pcr_gpu": "pcr"}
STAGE_ORDER = ["build", "gpucheck", "anchor", "timers", "residual_sweep"] + TIMING_ARMS + ["endpoints"]
STAGE_GROUPS = {"extract": ["build", "gpucheck"],
                "generate": ["anchor", "timers", "residual_sweep"] + TIMING_ARMS}

ARM_TEXT = {
    "thomas_gpu": "one system solved by the Thomas algorithm on one CUDA thread (thomas_gpu)",
    "pcr_gpu": "one system solved by parallel cyclic reduction, one thread per equation per round (pcr_gpu)",
    "cusparse_gpu": "one system solved by NVIDIA cuSPARSE gtsv2_nopivot (cusparse_gpu)",
    "thomas_batched_gpu": ("K copies of one system solved at once by the same one-thread Thomas kernel, "
                           "one block per copy (thomas_batched_gpu)"),
    "launch_probe": "an empty CUDA kernel launched with the level's PCR grid shape; ms per launch (launch_probe)",
    "cpu_dgtsv": "one system solved by LAPACK dgtsv through scipy on one CPU core (cpu_dgtsv)",
}

EXPECTED_RECORDS = (["toolchain", "gpu_check"] + [f"I{k}" for k in range(2, 11)] + ["gate_propagation"]
                    + ["I1_exact", "I1_perturbed", "I1_references", "E1", "E2", "timers", "residual_sweep"]
                    + TIMING_ARMS + ["timing_rows_check", "dispersion"] + [f"E{k}" for k in range(3, 11)])

# Decision rules, stated before any value is known (the record writer's convention).
RULES = {
    "toolchain": ("PASS iff numpy and scipy.linalg import, nvcc is found (PATH, then /usr/local/cuda/bin, then "
                  "/usr/local/cuda-*/bin), the CUDA source compiles with the fixed command, and the library "
                  "loads. Otherwise FAIL, run_valid false, exit 2. A missing cuSPARSE library alone does not "
                  "fail: its arm is NOT_RUN and the anchor reads against scipy alone."),
    "gpu_check": ("PASS iff cudaGetDeviceCount through ctypes returns success and at least 1 device. Otherwise "
                  "FAIL, run_valid false, exit 3, no CPU-only fallback."),
    "I1_exact": ("x* = ones at N = 2^10, seed 0, d = A x*. The residual readout of x* itself must be <= 1e-14. "
                 "Otherwise FAIL and run_valid false."),
    "I1_perturbed": ("x* perturbed by 1e-6 relative (alternating signs). The residual readout must lie in "
                     "[1e-7, 1e-5]. Otherwise FAIL and run_valid false."),
    "I1_references": ("On the same planted system, cuSPARSE and scipy solve_banded must agree to < 1e-8 relative "
                      "difference. Otherwise FAIL and run_valid false. NOT_RUN when cuSPARSE is missing."),
    "E1": ("Thomas and PCR at N = 2^10 and 2^14, seed 0: each relative residual <= 1e-10 AND each relative "
           "difference against cuSPARSE and against scipy < 1e-8. A solver out of band: its timing rows are "
           "labelled 'descriptive only; anchor failed' and E3, E4, E5 are NOT_READ; the box continues. "
           "cuSPARSE against scipy >= 1e-8: run_valid false in every record written after. cuSPARSE missing: "
           "read against scipy alone, label 'one reference only'."),
    "E2": ("Max relative residual over the anchor levels and both hand-written solvers. HOLDS if within "
           "[1e-14, 1e-12]. Below: REFUTED, the guess 1e-13 was too pessimistic. Above: REFUTED, too optimistic."),
    "E3": ("speedup(N) = median Thomas ms / median PCR ms over the five seeds. if_lever iff speedup(2^24) >= 2 "
           "AND speedup(2^24) > speedup(2^10) AND the least-squares slope of ln(speedup) against log2(N) over "
           "the five levels > 0. Otherwise if_not. Label 'within noise' when if_lever and the lower quartile of "
           "the per-seed ratio Thomas_ms / PCR_ms at 2^24 is <= 2. NOT_READ if the anchor failed for either."),
    "E4": ("Crossover = smallest level at which the lower quartile over seeds of Thomas_ms / PCR_ms exceeds 1. "
           "HOLDS iff the crossover is 2^10. Higher or none: REFUTED. Label 'crossover at 2^10 is launch-bound' "
           "when the PCR launch fraction at 2^10 is > 0.5. NOT_READ if the anchor failed for either solver."),
    "E5": ("Measured speedup(2^24) against the card's proxy 28. HOLDS if within [9.3, 84]. Outside: REFUTED, "
           "direction and ratio (measured / 28) reported. NOT_READ if the anchor failed for either solver."),
    "E6": ("g = (median PCR ms at 2^24 / median PCR ms at 2^22)^(1/2). log-like if g <= 1.15; linear-like if "
           "g >= 1.7; between otherwise. Report only."),
    "E7": ("E3's rule with median scipy dgtsv ms on one CPU core in place of the one-thread GPU Thomas ms. "
           "if_lever or if_not under that baseline, speedup at every level. Report only."),
    "E8": ("ratio(N) = median batched Thomas ms / median single Thomas ms; throughput factor K / ratio. The "
           "card's copies claim HOLDS if the ratio is within [0.9, 3] at every level. Otherwise FAILS, labelled "
           "'batched solve changes one system's latency'. Report only."),
    "E9": "Median cuSPARSE ms at each level and ratio = median PCR ms / median cuSPARSE ms. Report only.",
    "E10": ("Hours from the first anchor solve to the last sweep row. HOLDS if within [0.67, 6]. Below 0.67: "
            "REFUTED, the plan over-bought by more than 3x. Above 6: REFUTED, the plan under-bought."),
    "timers": ("A 100 ms time.sleep measures within +/- 5 ms; a cudaEvent-timed PCR block at N = 2^14 agrees "
               "with perf_counter around it within 5%; a block of 2R solves takes 2x the block of R within 15% "
               "for Thomas and for PCR at N = 2^14. All three PASS, otherwise FAIL and run_valid false."),
    "residual_sweep": "Report only: relative residual of one Thomas and one PCR solve per level and seed.",
    "arm": ("MEASURED iff every level has all five seeds with positive, finite ms per solve; otherwise "
            "INCOMPLETE. The anchor label of the solver is appended when it failed."),
    "timing_rows_check": ("PASS iff no timing row has non-positive or non-finite ms, a non-finite solution, or "
                          "a nonzero solver status. Otherwise FAIL and run_valid false."),
    "dispersion": ("The noise-rule quantity is the per-seed ratio over five generated systems. If its "
                   "interquartile range is exactly zero at any level, the wrong variance source was chosen: "
                   "WRONG_VARIANCE_SOURCE, run_valid false, the endpoints stage halts."),
    "planted": "PASS iff the endpoint arithmetic reproduces every planted known decision; otherwise FAIL, void.",
    "gate_propagation": ("PASS iff a planted Thomas anchor failure (residual 1e-9) labels Thomas rows and writes "
                         "E3, E4, E5 NOT_READ, and a planted reference disagreement (1e-7) writes run_valid "
                         "false into every record and row written after it. Otherwise FAIL and run_valid false."),
}


_LOG_TAG = [""]   # set while a planted control runs in a temporary directory, so its log lines say so


def log(msg: str) -> None:
    print(f"[m2 {time.strftime('%H:%M:%S')}] {_LOG_TAG[0]}{msg}", flush=True)


# ------------------------------------------------------------------------------------------------------------
# CUDA C source. Written to results_m2/build/m2_kernels.cu by the build stage, hashed, compiled with nvcc.
# ------------------------------------------------------------------------------------------------------------
CUDA_SOURCE = r"""// m2_kernels.cu: written by run_m2.py (build stage); its sha256 is recorded in env.json.
// Thomas: one CUDA thread per system, recurrence carried in registers; plain, no unroll, no variant search.
// PCR: one thread per equation per round, strides 1, 2, 4, ..., N/2, one launch per round, 256 threads a block.
// Thin C wrappers: device memory, cudaEvent timing of a block of R back-to-back solves, the cuSPARSE call.
#include <cuda_runtime.h>
#include <stddef.h>
#ifndef M2_NO_CUSPARSE
#include <cusparse.h>
#endif

#define M2_PCR_BLOCK 256
#define M2_SPARSE_BASE 100000

// Thomas, one thread per system. blockIdx.x picks the system; systems are laid out one after another.
// Forward: w = a_i / b'_{i-1}; b'_i = b_i - w c_{i-1}; d'_i = d_i - w d'_{i-1}. Back: x_i = (d'_i - c_i x_{i+1}) / b'_i.
__global__ void m2_thomas_kernel(const double* a, const double* b, const double* c, const double* d,
                                 double* bp, double* dp, double* x, int n)
{
    if (threadIdx.x != 0) return;
    const size_t off = (size_t)blockIdx.x * (size_t)n;
    a += off; b += off; c += off; d += off; bp += off; dp += off; x += off;
    double bprev = b[0];
    double dprev = d[0];
    double cprev = c[0];
    bp[0] = bprev;
    dp[0] = dprev;
    for (int i = 1; i < n; ++i) {
        const double w = a[i] / bprev;
        const double bi = b[i] - w * cprev;
        const double di = d[i] - w * dprev;
        bp[i] = bi;
        dp[i] = di;
        bprev = bi;
        dprev = di;
        cprev = c[i];
    }
    double xi = dprev / bprev;
    x[n - 1] = xi;
    for (int i = n - 2; i >= 0; --i) {
        xi = (dp[i] - c[i] * xi) / bp[i];
        x[i] = xi;
    }
}

// One PCR round at stride s. Coefficients outside [0, n) are zero. The last round writes x_i = d_i / b_i.
__global__ void m2_pcr_round(const double* a, const double* b, const double* c, const double* d,
                             double* a2, double* b2, double* c2, double* d2, double* x,
                             int n, int s, int last)
{
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    double alpha = 0.0, gamma = 0.0;
    double am = 0.0, cm = 0.0, dm = 0.0;
    double ap = 0.0, cp = 0.0, dq = 0.0;
    const int im = i - s;
    const int ip = i + s;
    if (im >= 0) { alpha = -a[i] / b[im]; am = a[im]; cm = c[im]; dm = d[im]; }
    if (ip < n)  { gamma = -c[i] / b[ip]; ap = a[ip]; cp = c[ip]; dq = d[ip]; }
    const double nb = b[i] + alpha * cm + gamma * ap;
    const double nd = d[i] + alpha * dm + gamma * dq;
    if (last) { x[i] = nd / nb; return; }
    a2[i] = alpha * am;
    b2[i] = nb;
    c2[i] = gamma * cp;
    d2[i] = nd;
}

__global__ void m2_empty_kernel(void) {}

// log2(n) rounds; round 0 reads the inputs, later rounds ping-pong between the two buffer sets.
static void m2_pcr_launch(int n, const double* a, const double* b, const double* c, const double* d,
                          double* const* buf, double* x)
{
    const int grid = (n + M2_PCR_BLOCK - 1) / M2_PCR_BLOCK;
    const double* ia = a; const double* ib = b; const double* ic = c; const double* id = d;
    int r = 0;
    for (int s = 1; s < n; s <<= 1, ++r) {
        double* const* o = buf + 4 * (r & 1);
        const int last = (2 * s >= n) ? 1 : 0;
        m2_pcr_round<<<grid, M2_PCR_BLOCK>>>(ia, ib, ic, id, o[0], o[1], o[2], o[3], x, n, s, last);
        ia = o[0]; ib = o[1]; ic = o[2]; id = o[3];
    }
}

typedef struct { cudaEvent_t e0; cudaEvent_t e1; } m2_timer;

static int m2_timer_start(m2_timer* t)
{
    int err = (int)cudaEventCreate(&t->e0);
    if (!err) err = (int)cudaEventCreate(&t->e1);
    if (!err) err = (int)cudaDeviceSynchronize();
    if (!err) err = (int)cudaEventRecord(t->e0, 0);
    return err;
}

static int m2_timer_stop(m2_timer* t, float* ms)
{
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaEventRecord(t->e1, 0);
    if (!err) err = (int)cudaEventSynchronize(t->e1);
    if (!err) err = (int)cudaDeviceSynchronize();
    if (!err) err = (int)cudaEventElapsedTime(ms, t->e0, t->e1);
    return err;
}

static void m2_timer_free(m2_timer* t)
{
    if (t->e0) cudaEventDestroy(t->e0);
    if (t->e1) cudaEventDestroy(t->e1);
}

extern "C" {

int m2_device_count(int* n) { return (int)cudaGetDeviceCount(n); }
int m2_runtime_version(int* v) { return (int)cudaRuntimeGetVersion(v); }
int m2_driver_version(int* v) { return (int)cudaDriverGetVersion(v); }
const char* m2_error_string(int e) { return cudaGetErrorString((cudaError_t)e); }

int m2_has_cusparse(void)
{
#ifdef M2_NO_CUSPARSE
    return 0;
#else
    return 1;
#endif
}

int m2_malloc(void** p, size_t bytes) { return (int)cudaMalloc(p, bytes); }
int m2_free(void* p) { return (int)cudaFree(p); }
int m2_h2d(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyHostToDevice); }
int m2_d2h(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyDeviceToHost); }
int m2_d2d(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyDeviceToDevice); }
int m2_sync(void) { return (int)cudaDeviceSynchronize(); }

int m2_solve_thomas(int K, int n, const double* a, const double* b, const double* c, const double* d,
                    double* bp, double* dp, double* x)
{
    m2_thomas_kernel<<<K, 1>>>(a, b, c, d, bp, dp, x, n);
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaDeviceSynchronize();
    return err;
}

int m2_time_thomas(int R, int K, int n, const double* a, const double* b, const double* c, const double* d,
                   double* bp, double* dp, double* x, float* ms)
{
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_thomas_kernel<<<K, 1>>>(a, b, c, d, bp, dp, x, n);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

int m2_solve_pcr(int n, const double* a, const double* b, const double* c, const double* d,
                 double* p0, double* p1, double* p2, double* p3, double* p4, double* p5, double* p6, double* p7,
                 double* x)
{
    double* buf[8] = {p0, p1, p2, p3, p4, p5, p6, p7};
    m2_pcr_launch(n, a, b, c, d, buf, x);
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaDeviceSynchronize();
    return err;
}

int m2_time_pcr(int R, int n, const double* a, const double* b, const double* c, const double* d,
                double* p0, double* p1, double* p2, double* p3, double* p4, double* p5, double* p6, double* p7,
                double* x, float* ms)
{
    double* buf[8] = {p0, p1, p2, p3, p4, p5, p6, p7};
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_pcr_launch(n, a, b, c, d, buf, x);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

int m2_time_empty(int R, int grid, int block, float* ms)
{
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_empty_kernel<<<grid, block>>>();
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

#ifndef M2_NO_CUSPARSE
static cusparseHandle_t m2_sparse = 0;

int m2_cusparse_init(void)
{
    if (m2_sparse) return 0;
    int st = (int)cusparseCreate(&m2_sparse);
    return st ? M2_SPARSE_BASE + st : 0;
}

int m2_cusparse_bufsize(int m, const double* dl, const double* d, const double* du, const double* B, size_t* bytes)
{
    int st = (int)cusparseDgtsv2_nopivot_bufferSizeExt(m2_sparse, m, 1, dl, d, du, B, m, bytes);
    return st ? M2_SPARSE_BASE + st : 0;
}

int m2_cusparse_solve(int m, const double* dl, const double* d, const double* du, double* B, void* buf)
{
    int st = (int)cusparseDgtsv2_nopivot(m2_sparse, m, 1, dl, d, du, B, m, buf);
    if (st) return M2_SPARSE_BASE + st;
    return (int)cudaDeviceSynchronize();
}

// R solves, each on its own copy of the right-hand side (B_all holds R copies laid out one after another).
int m2_time_cusparse(int R, int m, const double* dl, const double* d, const double* du, double* B_all, void* buf,
                     float* ms)
{
    m2_timer t = {0, 0};
    int st = 0;
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R && !st; ++r)
            st = (int)cusparseDgtsv2_nopivot(m2_sparse, m, 1, dl, d, du, B_all + (size_t)r * (size_t)m, m, buf);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    if (st) return M2_SPARSE_BASE + st;
    return err;
}
#endif

}  // extern "C"
"""

# Functions the Python side binds; the selftest checks each is defined in the source above.
CUDA_EXPORTS = ["m2_device_count", "m2_runtime_version", "m2_driver_version", "m2_error_string",
                "m2_has_cusparse", "m2_malloc", "m2_free", "m2_h2d", "m2_d2h", "m2_d2d", "m2_sync",
                "m2_solve_thomas", "m2_time_thomas", "m2_solve_pcr", "m2_time_pcr", "m2_time_empty"]
CUSPARSE_EXPORTS = ["m2_cusparse_init", "m2_cusparse_bufsize", "m2_cusparse_solve", "m2_time_cusparse"]


def nvcc_command(nvcc: str, cu: str, so: str, arch: str | None, cusparse: bool) -> list:
    """The execution note's command, verbatim; -arch=sm_80 only for an A100; no cuSPARSE when it is missing."""
    cmd = [nvcc, "-O3", "-shared", "-Xcompiler", "-fPIC"]
    if not cusparse:
        cmd.append("-DM2_NO_CUSPARSE")
    cmd += ["-o", so, cu]
    if cusparse:
        cmd.append("-lcusparse")
    cmd.append("-lcudart")
    if arch:
        cmd.append(f"-arch={arch}")
    return cmd


# ------------------------------------------------------------------------------------------------------------
# Parsers (each covered by the selftest)
# ------------------------------------------------------------------------------------------------------------
def parse_nvcc_version(text: str | None) -> str | None:
    m = re.search(r"release\s+([0-9]+\.[0-9]+),\s*V([0-9][0-9.]*)", text or "")
    return f"{m.group(1)} (V{m.group(2)})" if m else None


def parse_nvidia_smi_csv(text: str | None) -> dict:
    line = next((ln for ln in (text or "").splitlines() if ln.strip()), "")
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2 or not parts[0]:
        return {"gpu_name": None, "gpu_driver": None, "gpu_memory": None}
    return {"gpu_name": parts[0], "gpu_driver": parts[1], "gpu_memory": parts[2] if len(parts) > 2 else None}


def format_cuda_version(v) -> str | None:
    if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
        return None
    return f"{v // 1000}.{(v % 1000) // 10}"


def parse_blas_vendor(text: str | None) -> str:
    """Vendor from scipy.show_config text. New style names it ('blas: ... name: openblas'). Old style lists
    sections; sections marked NOT AVAILABLE are skipped and only their 'libraries = [...]' lists are read."""
    t = text or ""
    m = re.search(r"^[ \t]*blas:[ \t]*\n(?:[ \t]+.*\n)*?[ \t]+name:[ \t]*(\S+)", t, re.M)
    if m:
        return m.group(1).strip().lower()
    libs = []
    for _sec, body in re.findall(r"^(\S+):[ \t]*\n((?:[ \t]+.*(?:\n|$))*)", t, re.M):
        if "NOT AVAILABLE" in body:
            continue
        for lm in re.finditer(r"libraries\s*=\s*\[([^\]]*)\]", body):
            libs += [x.strip().strip("'\"").lower() for x in lm.group(1).split(",") if x.strip()]
    for key in ("mkl", "openblas", "blis", "flexiblas", "accelerate", "atlas"):
        if any(key in lib for lib in libs):
            return key
    if libs:
        return "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries"
    return "unknown"


def parse_ldd(text: str | None) -> dict:
    """ldd output -> {library name: resolved path, or None when 'not found'}."""
    libs = {}
    for line in (text or "").splitlines():
        m = re.match(r"\s*(\S+)\s+=>\s+(not found|\S+)", line)
        if m:
            libs[m.group(1)] = None if m.group(2) == "not found" else m.group(2)
    return libs


def parse_uptime(text: str | None) -> float | None:
    try:
        v = float((text or "").split()[0])
    except (IndexError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def parse_positive_float(s) -> float | None:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def parse_nonneg_float(s) -> float | None:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def detect_cusparse_missing(log_text: str | None) -> bool:
    t = (log_text or "").lower()
    keys = ("cannot find", "no such file", "not found", "undefined reference", "cannot open shared object")
    return "cusparse" in t and any(k in t for k in keys)


def cuda_dir_version_key(path: str) -> tuple:
    m = re.search(r"cuda-(\d+)\.(\d+)", path)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def read_jsonl(path) -> list:
    rows = []
    with open(path) as f:
        for k, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{k}: malformed row ({e})") from None
    return rows


# ------------------------------------------------------------------------------------------------------------
# Small statistics, stdlib only. Quartiles use linear interpolation (index (n-1) q, numpy's default).
# ------------------------------------------------------------------------------------------------------------
def is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def pos_finite(x) -> bool:
    return is_num(x) and math.isfinite(x) and x > 0


def le(x, t) -> bool:
    return is_num(x) and math.isfinite(x) and x <= t


def lt(x, t) -> bool:
    return is_num(x) and math.isfinite(x) and x < t


def median(xs) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        raise ValueError("median of nothing")
    return float(s[n // 2]) if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def quantile(xs, q: float) -> float:
    s = sorted(xs)
    if not s:
        raise ValueError("quantile of nothing")
    pos = (len(s) - 1) * q
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return float(s[lo] + (s[hi] - s[lo]) * (pos - lo))


def iqr(xs) -> float:
    return quantile(xs, 0.75) - quantile(xs, 0.25)


def ls_slope(xs, ys) -> float:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx


def same4(a, b) -> bool:
    """Equal to 4 significant digits."""
    return ("%.4g" % a) == ("%.4g" % b)


def fmt(x) -> str:
    return "%.4g" % x if is_num(x) else str(x)


# ------------------------------------------------------------------------------------------------------------
# Rules for R, K and launch fraction
# ------------------------------------------------------------------------------------------------------------
def r_rule(warm_ms: float) -> int:
    """R = max(1, ceil(50 ms / warm-up ms per solve)); the second warm-up solve's ms is used."""
    return max(1, int(math.ceil(BLOCK_MS / warm_ms)))


def k_rule(N: int) -> int:
    return min(K_CAP, K_TOTAL // N)


def log2_int(N: int) -> int:
    return int(round(math.log2(N)))


def launch_fraction(N: int, ms_per_launch: float, ms_per_solve: float) -> float:
    return log2_int(N) * ms_per_launch / ms_per_solve


# ------------------------------------------------------------------------------------------------------------
# Degenerate-output detectors
# ------------------------------------------------------------------------------------------------------------
def detect_bad_vector(xs) -> str | None:
    """A solution that cannot be a solve: empty, non-finite values, or all zeros."""
    vals = [float(v) for v in xs]
    if not vals:
        return "empty"
    if any(not math.isfinite(v) for v in vals):
        return "non-finite values"
    if all(v == 0.0 for v in vals):
        return "all zeros"
    return None


def detect_bad_timing_row(r: dict) -> str | None:
    if r.get("kind") != "timing":
        return None
    for key in ("ms_per_solve", "block_ms"):
        if not pos_finite(r.get(key)):
            return f"{key} not positive and finite ({r.get(key)!r})"
    if not (isinstance(r.get("R"), int) and r["R"] >= 1):
        return f"R not a positive integer ({r.get('R')!r})"
    if r.get("x_finite") is False:
        return "solution not finite"
    if r.get("solver_status") not in (None, 0):
        return f"solver status {r.get('solver_status')!r}"
    if r.get("degenerate"):
        return str(r["degenerate"])
    return None


def ms_table(rows, key: str = "ms_per_solve") -> dict:
    """Timing rows -> {N: {seed: value}}."""
    t: dict = {}
    for r in rows:
        if r.get("kind") != "timing":
            continue
        t.setdefault(int(r["N"]), {})[int(r["seed"])] = r.get(key)
    return t


def table_complete(t: dict) -> bool:
    return all(N in t and all(pos_finite(t[N].get(s)) for s in SEEDS) for N in LEVELS)


def missing_cells(t: dict) -> list:
    return [[N, s] for N in LEVELS for s in SEEDS if not pos_finite(t.get(N, {}).get(s))]


# ------------------------------------------------------------------------------------------------------------
# Endpoint arithmetic (pure; the planted controls and the endpoints stage both call these)
# ------------------------------------------------------------------------------------------------------------
def decide_e1(levels: list) -> dict:
    """levels: [{"N", "thomas": {"res", "diff_cusparse", "diff_scipy"}, "pcr": {...}, "ref_diff"}]."""
    one_ref = any(lv.get("ref_diff") is None for lv in levels)
    ok, reasons = {}, []
    for s in ("thomas", "pcr"):
        good = True
        for lv in levels:
            r = lv[s].get("res")
            if not le(r, RES_TOL):
                good = False
                reasons.append(f"{s} residual {fmt(r)} not <= {RES_TOL:g} at N={lv['N']}")
            for ref in ("cusparse", "scipy"):
                dv = lv[s].get("diff_" + ref)
                if dv is None and (ref == "cusparse" and one_ref):
                    continue
                if not lt(dv, DIFF_TOL):
                    good = False
                    reasons.append(f"{s} differs from {ref} by {fmt(dv)}, not < {DIFF_TOL:g}, at N={lv['N']}")
        ok[s] = good
    agree = None
    if not one_ref:
        agree = all(lt(lv.get("ref_diff"), DIFF_TOL) for lv in levels)
        if not agree:
            reasons.append("the two references (cuSPARSE, scipy) disagree by >= 1e-8: "
                           + ", ".join(f"N={lv['N']}: {fmt(lv.get('ref_diff'))}" for lv in levels))
    passed = ok["thomas"] and ok["pcr"] and agree is not False
    decision = "PASS" if passed else "FAIL: " + "; ".join(reasons)
    if one_ref:
        decision += f"; {LABEL_ONE_REF}"
    return {"decision": decision, "solver_ok": ok, "references_agree": agree, "one_reference_only": one_ref,
            "reasons": reasons}


def decide_e2(max_res) -> dict:
    lo, hi = E2_BAND
    if not (is_num(max_res) and math.isfinite(max_res)):
        return {"decision": "NOT_READ: residual not finite", "direction": None, "max_residual": max_res}
    if lo <= max_res <= hi:
        return {"decision": "HOLDS", "direction": None, "max_residual": max_res}
    if max_res < lo:
        return {"decision": "REFUTED", "direction": "too pessimistic", "max_residual": max_res,
                "guess_over_measured": E2_GUESS / max_res if max_res > 0 else None}
    return {"decision": "REFUTED", "direction": "too optimistic", "max_residual": max_res,
            "measured_over_guess": max_res / E2_GUESS}


def speedup_table(num: dict, den: dict) -> list:
    """num, den: {N: {seed: ms}}. speedup = median num / median den; per-seed ratio for the noise rule."""
    out = []
    for N in LEVELS:
        seeds = [s for s in SEEDS if s in num.get(N, {}) and s in den.get(N, {})]
        mn, md = median([num[N][s] for s in seeds]), median([den[N][s] for s in seeds])
        ratios = [num[N][s] / den[N][s] for s in seeds]
        out.append({"N": N, "log2_N": log2_int(N), "median_numerator_ms": mn, "median_denominator_ms": md,
                    "speedup": mn / md, "per_seed_ratio": ratios, "lower_quartile_ratio": quantile(ratios, 0.25),
                    "iqr_ratio": iqr(ratios)})
    return out


def decide_lever(table: list) -> dict:
    s = [r["speedup"] for r in table]
    x = [r["log2_N"] for r in table]
    slope = ls_slope(x, [math.log(v) for v in s])
    top_ok = s[-1] >= GATE_SPEEDUP
    above = s[-1] > s[0]
    lever = top_ok and above and slope > 0
    lq_top = table[-1]["lower_quartile_ratio"]
    label = "within noise" if (lever and lq_top <= GATE_SPEEDUP) else None
    decreases = [{"from_N": table[k]["N"], "to_N": table[k + 1]["N"], "from_speedup": s[k], "to_speedup": s[k + 1]}
                 for k in range(len(s) - 1) if s[k + 1] < s[k]]
    return {"decision": "if_lever" if lever else "if_not", "label": label, "speedups": s,
            "slope_ln_speedup_per_log2N": slope, "speedup_top_at_least_2": top_ok,
            "speedup_top_above_bottom": above, "slope_positive": slope > 0, "lower_quartile_top": lq_top,
            "adjacent_decreases": decreases}


def lever_from_tables(num: dict, den: dict) -> dict:
    tab = speedup_table(num, den)
    r = decide_lever(tab)
    r["table"] = tab
    return r


def decide_e4(lqs: list) -> dict:
    cross = next((N for N, q in zip(LEVELS, lqs) if q > 1.0), None)
    return {"decision": "HOLDS" if cross == LEVELS[0] else "REFUTED", "crossover_N": cross,
            "lower_quartiles": list(lqs)}


def decide_e5(s_top: float) -> dict:
    lo, hi = E5_BAND
    ratio = s_top / E5_PROXY
    if lo <= s_top <= hi:
        return {"decision": "HOLDS", "direction": None, "speedup_top": s_top, "measured_over_proxy": ratio}
    return {"decision": "REFUTED", "direction": "above" if s_top > hi else "below", "speedup_top": s_top,
            "measured_over_proxy": ratio}


def decide_e6(m22: float, m24: float) -> dict:
    g = math.sqrt(m24 / m22)
    shape = "log-like" if g <= E6_LOG_MAX else ("linear-like" if g >= E6_LIN_MIN else "between")
    return {"decision": shape, "g": g, "median_pcr_ms_2e22": m22, "median_pcr_ms_2e24": m24}


def decide_e8(ratios: list, ks: list) -> dict:
    lo, hi = E8_BAND
    holds = all(lo <= r <= hi for r in ratios)
    return {"decision": "HOLDS" if holds else "FAILS",
            "label": None if holds else "batched solve changes one system's latency",
            "ratios": list(ratios), "K": list(ks), "throughput_factor": [k / r for k, r in zip(ks, ratios)]}


def decide_e9(cus: list, pcr: list) -> dict:
    return {"decision": "REPORTED", "median_cusparse_ms": list(cus), "median_pcr_ms": list(pcr),
            "pcr_over_cusparse": [p / c for p, c in zip(pcr, cus)]}


def decide_e10(hours: float) -> dict:
    lo, hi = E10_BAND
    if lo <= hours <= hi:
        return {"decision": "HOLDS", "direction": None, "hours": hours}
    if hours < lo:
        return {"decision": "REFUTED", "direction": "below: the plan over-bought by more than 3x", "hours": hours}
    return {"decision": "REFUTED", "direction": "above: the plan under-bought", "hours": hours}


def check_timers(sleep_ms: float, event_ms: float, wall_ms: float, blocks: dict) -> dict:
    """blocks: {solver: (R, block_R_ms, block_2R_ms)}."""
    sleep_ok = is_num(sleep_ms) and abs(sleep_ms - TIMER_SLEEP_MS) <= TIMER_SLEEP_TOL_MS
    rel = abs(event_ms - wall_ms) / wall_ms if pos_finite(wall_ms) and is_num(event_ms) else float("inf")
    event_ok = rel <= TIMER_EVENT_TOL
    per = {}
    for solver, (R, b1, b2) in blocks.items():
        ratio = b2 / b1 if pos_finite(b1) and is_num(b2) else float("inf")
        per[solver] = {"R": R, "block_R_ms": b1, "block_2R_ms": b2, "ratio": ratio,
                       "ok": abs(ratio / 2.0 - 1.0) <= TIMER_2R_TOL}
    ok = sleep_ok and event_ok and all(p["ok"] for p in per.values())
    return {"ok": ok, "sleep_ms": sleep_ms, "sleep_ok": sleep_ok, "event_ms": event_ms, "wall_ms": wall_ms,
            "event_vs_wall_rel": rel, "event_ok": event_ok, "two_r": per}


def decide_i1(res_exact, res_perturbed, ref_diff) -> dict:
    a = le(res_exact, I1_EXACT_TOL)
    b = is_num(res_perturbed) and math.isfinite(res_perturbed) and I1_BAND[0] <= res_perturbed <= I1_BAND[1]
    c = None if ref_diff is None else lt(ref_diff, DIFF_TOL)
    return {"exact_ok": a, "perturbed_ok": b, "references_ok": c}


def guard_decision(remote_timeout: float, elapsed_s: float, uptime_s: float, price: float, budget: float):
    """Allowed seconds for the next stage, or STOP. Spend clock = box uptime x price per hour."""
    time_left = remote_timeout - elapsed_s - GUARD_RESERVE_S
    spend_now = price * uptime_s / 3600.0
    budget_s = (budget - spend_now) * 3600.0 / price - GUARD_TEARDOWN_S
    allowed = int(math.floor(min(time_left, budget_s)))
    if allowed < GUARD_MIN_STAGE_S:
        which = "time guard" if time_left <= budget_s else "cost guard"
        return "STOP", (f"{which}: {allowed}s left (time left {int(time_left)}s of REMOTE_TIMEOUT "
                        f"{int(remote_timeout)}s; spend so far {spend_now:.2f} USD of {budget:.2f} USD)")
    return "RUN", allowed


# ------------------------------------------------------------------------------------------------------------
# Run-validity state, labels, records and rows
# ------------------------------------------------------------------------------------------------------------
def _prov():
    fz = str(HERE / "frozen")
    if fz not in sys.path:
        sys.path.insert(0, fz)
    sys.dont_write_bytecode = True   # leave no cache files inside frozen/
    import provenance  # noqa: E402  the frozen record writer
    return provenance


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def state_path(out: Path) -> Path:
    return Path(out) / "RUN_VALID.json"


def fresh_state() -> dict:
    return {"run_valid": True, "voids": [], "anchor_failed": [], "anchor_done": False,
            "one_reference_only": False, "cusparse_available": None}


def load_state(out: Path) -> dict:
    p = state_path(out)
    if p.exists():
        st = json.loads(p.read_text())
        for k, v in fresh_state().items():
            st.setdefault(k, v)
        return st
    return fresh_state()


def save_state(out: Path, st: dict) -> None:
    st = dict(st)
    st["updated_utc"] = time.time()
    _atomic_write(state_path(out), json.dumps(st, indent=2, sort_keys=True))


def init_state(out: Path) -> None:
    save_state(out, fresh_state())


def void(out: Path, by: str, reason: str) -> None:
    """A gate failed: run_valid is false in RUN_VALID.json and so in every record and row written after."""
    st = load_state(out)
    st["run_valid"] = False
    st["voids"].append({"by": by, "reason": reason, "utc": time.time()})
    save_state(out, st)
    log(f"VOID by {by}: {reason}")


def apply_e1(out: Path, e1: dict) -> None:
    st = load_state(out)
    failed = [s for s in ("thomas", "pcr") if not e1["solver_ok"][s]]
    for s in failed:
        if s not in st["anchor_failed"]:
            st["anchor_failed"].append(s)
    if e1["one_reference_only"]:
        st["one_reference_only"] = True
    st["anchor_done"] = True
    save_state(out, st)
    if e1["references_agree"] is False:
        void(out, "E1 anchor", "the two references (cuSPARSE, scipy solve_banded) disagree by >= 1e-8")
    if failed and ANCHOR_FAIL_VOIDS_RUN:
        void(out, "E1 anchor", f"anchor failed for {failed}")


def anchor_status(arm: str, st: dict) -> str | None:
    solver = ARM_SOLVER.get(arm)
    if solver is None:
        return None
    if solver in st.get("anchor_failed", []):
        return LABEL_ANCHOR_FAILED
    return "anchor passed" if st.get("anchor_done") else "anchor not run"


def load_labels(out: Path) -> dict:
    p = Path(out) / "env.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return {"env_json": "unreadable"}
    return {}


def full_labels(out: Path) -> dict:
    lab = {"card_dramaturg": LABEL_DRAMATURG, "baseline": LABEL_BASELINE}
    lab.update(load_labels(out))
    return lab


def describe(path: Path, n_items=None) -> dict:
    return _prov().describe_input(path, n_items)


def describe_rows(out: Path, name: str) -> dict:
    p = Path(out) / "rows" / f"{name}.jsonl"
    n = sum(1 for ln in p.read_text().splitlines() if ln.strip()) if p.exists() else None
    return describe(p, n)


def code_inputs() -> list:
    return [describe(HERE / "run_m2.py")]


def write_record(out: Path, rid: str, kind: str, metric: str, values: dict, threshold: dict, rule: str,
                 decision: str, notes: str = "", rows=None, inputs=None, role: str | None = None) -> Path:
    prov = _prov()
    st = load_state(out)
    vals = dict(values)
    vals["run_valid"] = st["run_valid"]
    vals["anchor_failed"] = list(st["anchor_failed"])
    vals["one_reference_only"] = st["one_reference_only"]
    vals["labels"] = full_labels(out)
    if role:
        vals["role"] = role
    cell = {"run": TAG, "kind": kind, "id": rid}
    path = Path(out) / "records" / (prov.cell_slug(cell) + ".json")
    prov.write_result(path, cell=cell, inputs=list(inputs or []), metric=metric, values=vals,
                      threshold=threshold, decision_rule=rule, decision=decision, notes=notes, rows=rows)
    log(f"record {rid}: {decision[:160]}{' [run_valid=false]' if not st['run_valid'] else ''}")
    return path


class Rows:
    """One JSON line per measurement, verbatim. Each row carries run_valid as it stood when written."""

    def __init__(self, out: Path, name: str, arm: str | None = None):
        self.out, self.arm = Path(out), arm
        self.path = self.out / "rows" / f"{name}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(self.path, "w")
        self.labels = full_labels(self.out)
        self.n = 0

    def write(self, row: dict, t: float | None = None) -> dict:
        st = load_state(self.out)
        r = dict(row)
        if self.arm:
            r.setdefault("arm", self.arm)
            r["anchor_status"] = anchor_status(self.arm, st)
        r["run_valid"] = st["run_valid"]
        r["anchor_failed"] = list(st["anchor_failed"])
        r["one_reference_only"] = st["one_reference_only"]
        r["labels"] = self.labels
        r["t_written_utc"] = time.time() if t is None else t
        self.f.write(json.dumps(r, sort_keys=True) + "\n")
        self.f.flush()
        self.n += 1
        return r

    def close(self) -> None:
        self.f.close()


def read_rows(out: Path, name: str) -> list:
    p = Path(out) / "rows" / f"{name}.jsonl"
    return read_jsonl(p) if p.exists() else []


def read_records(out: Path) -> dict:
    recs = {}
    for p in sorted((Path(out) / "records").glob("*.json")):
        r = json.loads(p.read_text())
        recs[r["cell"]["id"]] = r
    return recs


# ------------------------------------------------------------------------------------------------------------
# Pure-Python solvers (selftest only; they mirror the CUDA kernels' arithmetic)
# ------------------------------------------------------------------------------------------------------------
def thomas_py(a, b, c, d) -> list:
    n = len(d)
    bp, dp = [0.0] * n, [0.0] * n
    bp[0], dp[0] = b[0], d[0]
    for i in range(1, n):
        w = a[i] / bp[i - 1]
        bp[i] = b[i] - w * c[i - 1]
        dp[i] = d[i] - w * dp[i - 1]
    x = [0.0] * n
    x[n - 1] = dp[n - 1] / bp[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = (dp[i] - c[i] * x[i + 1]) / bp[i]
    return x


def pcr_py(a, b, c, d):
    n = len(d)
    A, B, C, D = list(a), list(b), list(c), list(d)
    s, rounds, x = 1, 0, None
    while s < n:
        last = 2 * s >= n
        A2, B2, C2, D2, xn = [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n
        for i in range(n):
            alpha = gamma = am = cm = dm = ap = cp = dq = 0.0
            if i - s >= 0:
                alpha = -A[i] / B[i - s]
                am, cm, dm = A[i - s], C[i - s], D[i - s]
            if i + s < n:
                gamma = -C[i] / B[i + s]
                ap, cp, dq = A[i + s], C[i + s], D[i + s]
            nb = B[i] + alpha * cm + gamma * ap
            nd = D[i] + alpha * dm + gamma * dq
            if last:
                xn[i] = nd / nb
            else:
                A2[i], B2[i], C2[i], D2[i] = alpha * am, nb, gamma * cp, nd
        rounds += 1
        if last:
            x = xn
        A, B, C, D = A2, B2, C2, D2
        s <<= 1
    return x, rounds


def matvec_py(a, b, c, x) -> list:
    n = len(x)
    y = [b[i] * x[i] for i in range(n)]
    for i in range(1, n):
        y[i] += a[i] * x[i - 1]
    for i in range(n - 1):
        y[i] += c[i] * x[i + 1]
    return y


def norm_py(v) -> float:
    return math.sqrt(math.fsum(t * t for t in v))


def rel_residual_py(a, b, c, d, x) -> float:
    ax = matvec_py(a, b, c, x)
    return norm_py([p - q for p, q in zip(ax, d)]) / norm_py(d)


def rel_diff_py(x, xref) -> float:
    return norm_py([p - q for p, q in zip(x, xref)]) / norm_py(xref)


def alternating_signs(n: int) -> list:
    return [1.0 if i % 2 == 0 else -1.0 for i in range(n)]


def fingerprint(arr) -> dict:
    """First 8 values and sha256 of the float64 little-endian bytes; lists and numpy arrays agree."""
    if hasattr(arr, "tobytes"):
        import numpy as np
        raw = np.ascontiguousarray(arr, dtype="<f8").tobytes()
        first = [float(v) for v in arr[:8]]
    else:
        raw = struct.pack("<%dd" % len(arr), *arr)
        first = [float(v) for v in arr[:8]]
    return {"first8": first, "sha256": hashlib.sha256(raw).hexdigest(), "n": len(arr)}


# ------------------------------------------------------------------------------------------------------------
# Box-only numerics (numpy, scipy, CUDA through ctypes). Imported lazily so the selftest stays stdlib-only.
# ------------------------------------------------------------------------------------------------------------
def _np():
    import numpy
    return numpy


def make_system(N: int, seed: int):
    """a_i, c_i random signs (a_0 = c_{N-1} = 0), b_i = 3, d_i standard normal; draws: a-signs, c-signs, d."""
    np = _np()
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 2, size=N).astype(np.float64) * 2.0 - 1.0
    c = rng.integers(0, 2, size=N).astype(np.float64) * 2.0 - 1.0
    d = rng.standard_normal(N)
    a[0] = 0.0
    c[N - 1] = 0.0
    b = np.full(N, B_DIAG, dtype=np.float64)
    return a, b, c, d


def system_row(N: int, seed: int, a, b, c, d, context: str) -> dict:
    return {"kind": "system", "N": N, "seed": seed, "context": context, "a": fingerprint(a),
            "b": fingerprint(b), "c": fingerprint(c), "d": fingerprint(d)}


def matvec_np(a, b, c, x):
    y = b * x
    y[1:] += a[1:] * x[:-1]
    y[:-1] += c[:-1] * x[1:]
    return y


def rel_residual_np(a, b, c, d, x) -> float:
    np = _np()
    return float(np.linalg.norm(matvec_np(a, b, c, x) - d) / np.linalg.norm(d))


def rel_diff_np(x, xref) -> float:
    np = _np()
    return float(np.linalg.norm(x - xref) / np.linalg.norm(xref))


def scipy_reference(a, b, c, d):
    np = _np()
    from scipy.linalg import solve_banded
    N = len(d)
    ab = np.zeros((3, N))
    ab[0, 1:] = c[:-1]
    ab[1, :] = b
    ab[2, :-1] = a[1:]
    return solve_banded((1, 1), ab, d)


def vec_flags(x) -> dict:
    np = _np()
    return {"x_finite": bool(np.isfinite(x).all()), "x_all_zero": bool((x == 0).all()),
            "x_first8": [float(v) for v in x[:8]]}


class Lib:
    """ctypes bindings to results_m2/build/libm2.so."""

    def __init__(self, so_path):
        self.path = str(so_path)
        L = ctypes.CDLL(self.path)
        self.L = L
        vp, ci, sz = ctypes.c_void_p, ctypes.c_int, ctypes.c_size_t
        pf, pi = ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int)

        def sig(name, argtypes, restype=ci):
            fn = getattr(L, name)
            fn.argtypes = argtypes
            fn.restype = restype

        sig("m2_device_count", [pi])
        sig("m2_runtime_version", [pi])
        sig("m2_driver_version", [pi])
        sig("m2_error_string", [ci], ctypes.c_char_p)
        sig("m2_has_cusparse", [])
        sig("m2_malloc", [ctypes.POINTER(vp), sz])
        sig("m2_free", [vp])
        sig("m2_h2d", [vp, vp, sz])
        sig("m2_d2h", [vp, vp, sz])
        sig("m2_d2d", [vp, vp, sz])
        sig("m2_sync", [])
        sig("m2_solve_thomas", [ci, ci] + [vp] * 7)
        sig("m2_time_thomas", [ci, ci, ci] + [vp] * 7 + [pf])
        sig("m2_solve_pcr", [ci] + [vp] * 13)
        sig("m2_time_pcr", [ci, ci] + [vp] * 13 + [pf])
        sig("m2_time_empty", [ci, ci, ci, pf])
        self.has_cusparse = bool(L.m2_has_cusparse())
        if self.has_cusparse:
            sig("m2_cusparse_init", [])
            sig("m2_cusparse_bufsize", [ci, vp, vp, vp, vp, ctypes.POINTER(sz)])
            sig("m2_cusparse_solve", [ci, vp, vp, vp, vp, vp])
            sig("m2_time_cusparse", [ci, ci, vp, vp, vp, vp, vp, pf])

    def err(self, code: int) -> str:
        if code >= SPARSE_BASE:
            return f"cuSPARSE status {code - SPARSE_BASE}"
        s = self.L.m2_error_string(code)
        return f"CUDA error {code} ({s.decode() if s else '?'})"

    def ck(self, code: int, what: str) -> None:
        if code:
            raise RuntimeError(f"{what}: {self.err(code)}")

    def device_count(self):
        n = ctypes.c_int(0)
        code = self.L.m2_device_count(ctypes.byref(n))
        return code, n.value

    def runtime_version(self):
        v = ctypes.c_int(0)
        code = self.L.m2_runtime_version(ctypes.byref(v))
        return code, v.value

    def driver_version(self):
        v = ctypes.c_int(0)
        code = self.L.m2_driver_version(ctypes.byref(v))
        return code, v.value

    def malloc(self, nbytes: int) -> int:
        p = ctypes.c_void_p()
        self.ck(self.L.m2_malloc(ctypes.byref(p), nbytes), f"cudaMalloc of {nbytes} bytes")
        return p.value

    def time_empty(self, R: int, grid: int, block: int) -> float:
        ms = ctypes.c_float()
        self.ck(self.L.m2_time_empty(R, grid, block, ctypes.byref(ms)), "empty-kernel block")
        return float(ms.value)


class GpuSystem:
    """Device arrays for one system (or K copies laid out one after another) and the solves on them."""

    def __init__(self, lib: Lib, N: int, K: int = 1, thomas: bool = False, pcr: bool = False):
        self.lib, self.N, self.K = lib, N, K
        self.ptrs: list = []
        nb = N * K * 8
        self.a, self.b, self.c, self.d = [self._alloc(nb) for _ in range(4)]
        self.bp = self.dp = self.xt = self.xp = self.sp_buf = None
        self.buf: list = []
        self.sp_bytes = None
        self.last_x = None
        if thomas:
            self.bp, self.dp, self.xt = [self._alloc(nb) for _ in range(3)]
        if pcr:
            self.buf = [self._alloc(N * 8) for _ in range(8)]
            self.xp = self._alloc(N * 8)

    def _alloc(self, nb: int) -> int:
        p = self.lib.malloc(nb)
        self.ptrs.append(p)
        return p

    def release(self, p: int) -> None:
        self.lib.L.m2_free(p)
        self.ptrs.remove(p)

    def free(self) -> None:
        for p in self.ptrs:
            self.lib.L.m2_free(p)
        self.ptrs = []

    def upload(self, a, b, c, d) -> None:
        L, nb1 = self.lib.L, self.N * 8
        for dst, arr in ((self.a, a), (self.b, b), (self.c, c), (self.d, d)):
            self.lib.ck(L.m2_h2d(dst, arr.ctypes.data, nb1), "copy system to the GPU")
            for k in range(1, self.K):
                self.lib.ck(L.m2_d2d(dst + k * nb1, dst, nb1), "copy system into a batch slot")
        self.lib.ck(L.m2_sync(), "synchronise after upload")

    def download(self, ptr: int):
        np = _np()
        out = np.empty(self.N, dtype=np.float64)
        self.lib.ck(self.lib.L.m2_d2h(out.ctypes.data, ptr, self.N * 8), "copy solution from the GPU")
        return out

    def thomas_solve(self) -> None:
        self.lib.ck(self.lib.L.m2_solve_thomas(self.K, self.N, self.a, self.b, self.c, self.d, self.bp, self.dp,
                                               self.xt), "Thomas solve")

    def thomas_block(self, R: int) -> float:
        ms = ctypes.c_float()
        self.lib.ck(self.lib.L.m2_time_thomas(R, self.K, self.N, self.a, self.b, self.c, self.d, self.bp,
                                              self.dp, self.xt, ctypes.byref(ms)), "Thomas timed block")
        return float(ms.value)

    def pcr_solve(self) -> None:
        self.lib.ck(self.lib.L.m2_solve_pcr(self.N, self.a, self.b, self.c, self.d, *self.buf, self.xp),
                    "PCR solve")

    def pcr_block(self, R: int) -> float:
        ms = ctypes.c_float()
        self.lib.ck(self.lib.L.m2_time_pcr(R, self.N, self.a, self.b, self.c, self.d, *self.buf, self.xp,
                                           ctypes.byref(ms)), "PCR timed block")
        return float(ms.value)

    def cusparse_prepare(self) -> None:
        """Handle and work buffer, allocated once per level outside any timed block."""
        L = self.lib.L
        self.lib.ck(L.m2_cusparse_init(), "cusparseCreate")
        size = ctypes.c_size_t(0)
        self.lib.ck(L.m2_cusparse_bufsize(self.N, self.a, self.b, self.c, self.d, ctypes.byref(size)),
                    "gtsv2_nopivot buffer size")
        self.sp_bytes = int(size.value)
        self.sp_buf = self._alloc(max(self.sp_bytes, 256))

    def cusparse_solve_copy(self):
        L, nb1 = self.lib.L, self.N * 8
        B = self._alloc(nb1)
        try:
            self.lib.ck(L.m2_d2d(B, self.d, nb1), "copy right-hand side")
            self.lib.ck(L.m2_cusparse_solve(self.N, self.a, self.b, self.c, B, self.sp_buf), "gtsv2_nopivot solve")
            x = self.download(B)
        finally:
            self.release(B)
        return x

    def cusparse_block(self, R: int) -> float:
        """R solves, each on its own copy of d made before the timed block (gtsv2 overwrites its B)."""
        L, nb1 = self.lib.L, self.N * 8
        B_all = self._alloc(R * nb1)
        try:
            for r in range(R):
                self.lib.ck(L.m2_d2d(B_all + r * nb1, self.d, nb1), "copy right-hand side")
            self.lib.ck(L.m2_sync(), "synchronise after copies")
            ms = ctypes.c_float()
            self.lib.ck(L.m2_time_cusparse(R, self.N, self.a, self.b, self.c, B_all, self.sp_buf,
                                           ctypes.byref(ms)), "gtsv2_nopivot timed block")
            self.last_x = self.download(B_all + (R - 1) * nb1)
        finally:
            self.release(B_all)
        return float(ms.value)


def time_cell(block_fn) -> dict:
    """2 warm-up solves (each timed only to size R), then one timed block of R back-to-back solves."""
    warm = [block_fn(1) for _ in range(WARMUPS)]
    degenerate = None
    if pos_finite(warm[-1]):
        R = r_rule(warm[-1])
    else:
        R = 1
        degenerate = f"second warm-up ms not positive and finite ({warm[-1]!r})"
    block = block_fn(R)
    return {"warmup_ms": warm, "R": R, "block_ms": block, "ms_per_solve": block / R,
            "block_at_least_50ms": bool(is_num(block) and block >= BLOCK_MS), "degenerate": degenerate}


def run_cmd(cmd, timeout=120, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, "", f"timed out after {timeout}s: {e}"


def find_nvcc() -> str | None:
    p = shutil.which("nvcc")
    if p:
        return p
    if os.access("/usr/local/cuda/bin/nvcc", os.X_OK):
        return "/usr/local/cuda/bin/nvcc"
    cands = [c for c in glob.glob("/usr/local/cuda-*/bin/nvcc") if os.access(c, os.X_OK)]
    cands.sort(key=cuda_dir_version_key)
    return cands[-1] if cands else None


def locate_libcudart(so_path: str, nvcc: str | None):
    rc, txt, _ = run_cmd(["ldd", so_path], timeout=30)
    for name, path in parse_ldd(txt).items():
        if name.startswith("libcudart.so") and path:
            return path, txt
    import ctypes.util
    name = ctypes.util.find_library("cudart")
    if name:
        return name, txt
    roots = []
    if nvcc:
        roots.append(os.path.join(os.path.dirname(os.path.dirname(nvcc)), "lib64"))
    roots += ["/usr/local/cuda/lib64", "/usr/lib/x86_64-linux-gnu"]
    for root in roots:
        g = sorted(glob.glob(os.path.join(root, "libcudart.so*")))
        if g:
            return g[-1], txt
    return None, txt


def try_load(so: Path) -> str | None:
    try:
        ctypes.CDLL(str(so))
        return None
    except OSError as e:
        return str(e)


def rel_to_here(p: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(HERE))
    except ValueError:
        return str(p)


# ------------------------------------------------------------------------------------------------------------
# Stages
# ------------------------------------------------------------------------------------------------------------
class Ctx:
    def __init__(self, out, build):
        self.out, self.build = Path(out), Path(build)
        self.so = self.build / "libm2.so"
        self.cu = self.build / "m2_kernels.cu"


def collect_base_labels() -> dict:
    return {
        "instance_type": os.environ.get("INSTANCE_TYPE") or "unset (INSTANCE_TYPE not in environment)",
        "price_usd_per_hour": parse_positive_float(os.environ.get("PRICE_USD_PER_HOUR")),
        "budget_left_usd": parse_nonneg_float(os.environ.get("BUDGET_LEFT_USD")),
        "vcpu_count": os.cpu_count(),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        "lambda_instance_id": os.environ.get("LAMBDA_INSTANCE_ID") or None,
        "git_commit": os.environ.get("GIT_COMMIT") or None,
        "python_version": sys.version.split()[0],
        "runner_sha256": hashlib.sha256((HERE / "run_m2.py").read_bytes()).hexdigest(),
    }


def stage_build(ctx: Ctx) -> int:
    out, build = ctx.out, ctx.build
    out.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    if not state_path(out).exists():
        init_state(out)
    labels = collect_base_labels()
    envtxt = [f"== utc {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}",
              f"== vcpu {os.cpu_count()}", f"== python {sys.version}"]
    metric = "toolchain check: numpy, scipy.linalg, nvcc, compile of the CUDA source, load of the library"
    threshold = {"nvcc_lookup": ["PATH", "/usr/local/cuda/bin/nvcc", "/usr/local/cuda-*/bin/nvcc"]}

    def save_labels():
        text = json.dumps(labels, indent=2, sort_keys=True)
        _atomic_write(out / "env.json", text)
        _atomic_write(out / "env.txt", "\n".join(envtxt) + "\n== labels carried by every record (env.json)\n"
                      + text + "\n")

    def fail(reason, values):
        labels["toolchain_failure"] = reason
        save_labels()
        void(out, "toolchain check", reason)
        write_record(out, "toolchain", "gate", metric, values, threshold, RULES["toolchain"], "FAIL: " + reason,
                     inputs=code_inputs())
        return EXIT_TOOLCHAIN

    try:
        import numpy
        import scipy
        import scipy.linalg
        import scipy.linalg.lapack  # noqa: F401
    except Exception as e:  # noqa: BLE001
        envtxt.append(f"== import failure\n{e!r}")
        return fail(f"numpy or scipy.linalg import failed: {e!r}", {"import_error": repr(e)})
    labels["numpy_version"] = numpy.__version__
    labels["scipy_version"] = scipy.__version__
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            scipy.show_config()
        except Exception as e:  # noqa: BLE001
            print(f"scipy.show_config failed: {e!r}")
    cfg = buf.getvalue()
    labels["blas_lapack_vendor"] = parse_blas_vendor(cfg)
    flapack = getattr(getattr(scipy.linalg, "_flapack", None), "__file__", None)
    lapack_libs = {}
    if flapack:
        _, ltxt, _ = run_cmd(["ldd", flapack], timeout=30)
        for name, path in parse_ldd(ltxt).items():
            if any(k in name for k in ("blas", "lapack", "mkl", "openblas")):
                lapack_libs[name] = {"path": path, "resolved": os.path.realpath(path) if path else None}
        envtxt += [f"== ldd {flapack}", ltxt]
    labels["scipy_lapack_libraries"] = lapack_libs
    envtxt += ["== numpy " + numpy.__version__ + " scipy " + scipy.__version__, "== scipy.show_config()", cfg]

    rc, smi, smierr = run_cmd(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                               "--format=csv,noheader"], timeout=60)
    labels.update(parse_nvidia_smi_csv(smi if rc == 0 else ""))
    rc2, smifull, _ = run_cmd(["nvidia-smi"], timeout=60)
    envtxt += ["== nvidia-smi --query-gpu", smi or smierr, "== nvidia-smi", smifull]

    nvcc = find_nvcc()
    labels["nvcc_path"] = nvcc
    if not nvcc:
        save_labels()
        return fail("nvcc not found on PATH, at /usr/local/cuda/bin/nvcc, or at /usr/local/cuda-*/bin/nvcc",
                    {"nvcc_path": None})
    rc, vout, verr = run_cmd([nvcc, "--version"], timeout=60)
    labels["nvcc_version"] = parse_nvcc_version(vout) or (vout or verr).strip()
    envtxt += ["== nvcc --version", vout or verr]

    _atomic_write(ctx.cu, CUDA_SOURCE)
    labels["kernel_source_sha256"] = hashlib.sha256(CUDA_SOURCE.encode()).hexdigest()
    arch = "sm_80" if labels.get("gpu_name") and "A100" in labels["gpu_name"] else None
    labels["nvcc_arch_flag"] = f"-arch={arch}" if arch else None
    cu_rel, so_rel = rel_to_here(ctx.cu), rel_to_here(ctx.so)
    cusparse, cus_note, compile_log = True, None, []

    def compile_once(with_cusparse):
        cmd = nvcc_command(nvcc, cu_rel, so_rel, arch, with_cusparse)
        log("compile: " + " ".join(cmd))
        code, so_out, so_err = run_cmd(cmd, timeout=900, cwd=str(HERE))
        compile_log.append({"command": cmd, "rc": code, "stdout": so_out[-4000:], "stderr": so_err[-4000:]})
        return cmd, code, so_out + so_err

    cmd, code, text = compile_once(True)
    if code != 0:
        if detect_cusparse_missing(text):
            cusparse = False
            cus_note = "cuSPARSE missing at compile or link time: " + text.strip().splitlines()[-1][:300]
            cmd, code, text = compile_once(False)
        if code != 0:
            _atomic_write(build / "compile.log", json.dumps(compile_log, indent=2))
            save_labels()
            return fail("nvcc compilation failed", {"compile": compile_log})
    load_err = try_load(ctx.so)
    if load_err and cusparse and "cusparse" in load_err.lower():
        cusparse = False
        cus_note = "cuSPARSE missing at load time: " + load_err[:300]
        cmd, code, text = compile_once(False)
        if code != 0:
            _atomic_write(build / "compile.log", json.dumps(compile_log, indent=2))
            save_labels()
            return fail("nvcc compilation without cuSPARSE failed", {"compile": compile_log})
        load_err = try_load(ctx.so)
    _atomic_write(build / "compile.log", json.dumps(compile_log, indent=2))
    labels["compile_command"] = " ".join(cmd)
    if load_err:
        save_labels()
        return fail(f"compiled library does not load: {load_err}", {"compile": compile_log, "load_error": load_err})
    labels["cusparse_available"] = cusparse
    labels["cusparse_note"] = cus_note
    lib = Lib(ctx.so)
    code, v = lib.runtime_version()
    labels["cuda_runtime_version_runner_library"] = format_cuda_version(v) if code == 0 else lib.err(code)
    path, ldd_txt = locate_libcudart(str(ctx.so), nvcc)
    envtxt += ["== ldd libm2.so", ldd_txt]
    labels["libcudart_path"] = path
    labels["cuda_runtime_version"] = labels["cuda_runtime_version_runner_library"]
    labels["cuda_runtime_version_via"] = "runner library wrapper (no shared libcudart located)"
    if path:
        try:
            cr = ctypes.CDLL(path)
            cr.cudaRuntimeGetVersion.argtypes = [ctypes.POINTER(ctypes.c_int)]
            cr.cudaRuntimeGetVersion.restype = ctypes.c_int
            vv = ctypes.c_int(0)
            if cr.cudaRuntimeGetVersion(ctypes.byref(vv)) == 0:
                labels["cuda_runtime_version"] = format_cuda_version(vv.value)
                labels["cuda_runtime_version_via"] = f"cudaRuntimeGetVersion via ctypes on {path}"
        except OSError as e:
            labels["libcudart_load_error"] = str(e)
    save_labels()
    st = load_state(out)
    st["cusparse_available"] = cusparse
    if not cusparse:
        st["one_reference_only"] = True
    save_state(out, st)
    decision = "PASS" if cusparse else ("PASS; cuSPARSE missing: its arm is NOT_RUN and the anchor reads "
                                        f"against scipy alone ({LABEL_ONE_REF})")
    write_record(out, "toolchain", "gate", metric,
                 {"nvcc_path": nvcc, "nvcc_version": labels["nvcc_version"], "compile": compile_log,
                  "cusparse_available": cusparse, "cusparse_note": cus_note,
                  "kernel_source_sha256": labels["kernel_source_sha256"]},
                 threshold, RULES["toolchain"], decision, inputs=code_inputs() + [describe(ctx.cu)])
    return EXIT_OK


def stage_gpucheck(ctx: Ctx) -> int:
    out = ctx.out
    labels = load_labels(out)
    vals = {}
    try:
        lib = Lib(ctx.so)
        code, n = lib.device_count()
        vals["via_runner_library"] = {"status": code, "device_count": n, "error": lib.err(code) if code else None}
        code_d, drv = lib.driver_version()
        vals["cuda_driver_api_version"] = format_cuda_version(drv) if code_d == 0 else None
    except Exception as e:  # noqa: BLE001
        vals["via_runner_library"] = {"status": -1, "device_count": 0, "error": repr(e)}
    path = labels.get("libcudart_path")
    if path:
        try:
            cr = ctypes.CDLL(path)
            cr.cudaGetDeviceCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
            cr.cudaGetDeviceCount.restype = ctypes.c_int
            n2 = ctypes.c_int(0)
            code2 = cr.cudaGetDeviceCount(ctypes.byref(n2))
            vals["via_libcudart"] = {"path": path, "status": code2, "device_count": n2.value}
        except OSError as e:
            vals["via_libcudart"] = {"path": path, "status": -1, "device_count": 0, "error": str(e)}
    checks = [v for k, v in vals.items() if k.startswith("via_")]
    ok = all(v.get("status") == 0 and v.get("device_count", 0) >= 1 for v in checks)
    rc, smi, _ = run_cmd(["nvidia-smi", "-L"], timeout=60)
    vals["nvidia_smi_list"] = smi.strip()
    with open(out / "env.txt", "a") as f:
        f.write("== gpu check\n" + json.dumps(vals, indent=2) + "\n")
    metric = "GPU check: cudaGetDeviceCount through ctypes"
    if not ok:
        void(out, "GPU check", f"no CUDA device visible: {json.dumps(vals)}")
        write_record(out, "gpu_check", "gate", metric, vals, {"min_devices": 1}, RULES["gpu_check"],
                     "FAIL: no CUDA device visible", inputs=code_inputs())
        return EXIT_GPU
    labels["gpu_device_count"] = vals["via_runner_library"]["device_count"]
    labels["cuda_driver_api_version"] = vals.get("cuda_driver_api_version")
    _atomic_write(out / "env.json", json.dumps(labels, indent=2, sort_keys=True))
    write_record(out, "gpu_check", "gate", metric, vals, {"min_devices": 1}, RULES["gpu_check"], "PASS",
                 inputs=code_inputs())
    return EXIT_OK


def write_planted_controls(out: Path) -> None:
    for ctl in planted_controls():
        if not ctl["ok"]:
            void(out, f"control {ctl['id']}", "planted arithmetic did not reproduce its known decisions")
        write_record(out, ctl["id"], "control", ctl["metric"], ctl["values"], ctl["threshold"], ctl["rule"],
                     "PASS" if ctl["ok"] else "FAIL", inputs=code_inputs())
    tmp = Path(tempfile.mkdtemp(prefix="m2_gate_propagation_"))
    try:
        ok, details = planted_gate_propagation(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not ok:
        void(out, "gate propagation control", "planted failures did not propagate as specified")
    write_record(out, "gate_propagation", "control",
                 "planted gate failures: Thomas anchor residual 1e-9; references disagreeing by 1e-7",
                 {"checks": details}, {"thomas_residual": 1e-9, "reference_difference": 1e-7},
                 RULES["gate_propagation"], "PASS" if ok else "FAIL", inputs=code_inputs())


def stage_anchor(ctx: Ctx) -> int:
    out = ctx.out
    np = _np()
    write_planted_controls(out)
    st = load_state(out)
    lib = Lib(ctx.so)
    cus = bool(lib.has_cusparse and st.get("cusparse_available"))
    rows, sysrows = Rows(out, "anchor"), Rows(out, "systems_anchor")

    # Readout control: planted known truth at N = 2^10, seed 0.
    N = ANCHOR_LEVELS[0]
    a, b, c, _d0 = make_system(N, ANCHOR_SEED)
    xstar = np.ones(N)
    d = matvec_np(a, b, c, xstar)
    sysrows.write(system_row(N, ANCHOR_SEED, a, b, c, d, "readout control: d = A x*, x* = ones"))
    res_exact = rel_residual_np(a, b, c, d, xstar)
    s = np.array(alternating_signs(N))
    xpert = xstar + I1_PERTURB * s * (np.linalg.norm(xstar) / np.linalg.norm(s))
    res_pert = rel_residual_np(a, b, c, d, xpert)
    t0 = time.time()
    x_sp = scipy_reference(a, b, c, d)
    t1 = time.time()
    rows.write({"kind": "readout_control", "solver": "scipy_solve_banded", "N": N, "seed": ANCHOR_SEED,
                "x": x_sp.tolist(), "x_fingerprint": fingerprint(x_sp), "t_start_utc": t0, "t_end_utc": t1,
                "rel_residual": rel_residual_np(a, b, c, d, x_sp), "diff_vs_xstar": rel_diff_np(x_sp, xstar)})
    ref_diff = None
    if cus:
        gs = GpuSystem(lib, N)
        try:
            gs.upload(a, b, c, d)
            gs.cusparse_prepare()
            t0 = time.time()
            x_cu = gs.cusparse_solve_copy()
            t1 = time.time()
        finally:
            gs.free()
        ref_diff = rel_diff_np(x_cu, x_sp)
        rows.write({"kind": "readout_control", "solver": "cusparse_gtsv2_nopivot", "N": N, "seed": ANCHOR_SEED,
                    "x": x_cu.tolist(), "x_fingerprint": fingerprint(x_cu), "t_start_utc": t0, "t_end_utc": t1,
                    "rel_residual": rel_residual_np(a, b, c, d, x_cu), "diff_vs_scipy": ref_diff,
                    "diff_vs_xstar": rel_diff_np(x_cu, xstar)})
    rows.write({"kind": "readout_control", "solver": "x_star_itself", "N": N, "seed": ANCHOR_SEED,
                "rel_residual_exact": res_exact, "rel_residual_perturbed": res_pert,
                "perturbation_relative_size": rel_diff_np(xpert, xstar)})
    i1 = decide_i1(res_exact, res_pert, ref_diff)
    base = {"N": N, "seed": ANCHOR_SEED}
    if not i1["exact_ok"]:
        void(out, "I1 exact readout", f"readout of x* is {res_exact!r}, not <= 1e-14")
    write_record(out, "I1_exact", "control", "residual readout of the exact solution x* = ones (d = A x*)",
                 dict(base, rel_residual=res_exact), {"max": I1_EXACT_TOL}, RULES["I1_exact"],
                 "PASS" if i1["exact_ok"] else "FAIL", inputs=[describe_rows(out, "anchor")])
    if not i1["perturbed_ok"]:
        void(out, "I1 perturbed readout", f"readout of perturbed x* is {res_pert!r}, outside [1e-7, 1e-5]")
    write_record(out, "I1_perturbed", "control", "residual readout of x* perturbed by 1e-6 relative",
                 dict(base, rel_residual=res_pert), {"band": list(I1_BAND)}, RULES["I1_perturbed"],
                 "PASS" if i1["perturbed_ok"] else "FAIL", inputs=[describe_rows(out, "anchor")])
    if i1["references_ok"] is False:
        void(out, "I1 references", f"cuSPARSE and scipy differ by {ref_diff!r} on the planted system")
    write_record(out, "I1_references", "control", "cuSPARSE against scipy solve_banded on the planted system",
                 dict(base, relative_difference=ref_diff), {"max_exclusive": DIFF_TOL}, RULES["I1_references"],
                 ("NOT_RUN: " + LABEL_ONE_REF) if ref_diff is None else ("PASS" if i1["references_ok"] else "FAIL"),
                 inputs=[describe_rows(out, "anchor")])

    # Anchor: N = 2^10 and 2^14, seed 0; Thomas, PCR, cuSPARSE, scipy.
    levels, rec_rows = [], []
    for N in ANCHOR_LEVELS:
        a, b, c, d = make_system(N, ANCHOR_SEED)
        sysrows.write(system_row(N, ANCHOR_SEED, a, b, c, d, "anchor"))
        gs = GpuSystem(lib, N, thomas=True, pcr=True)
        xs, times = {}, {}
        try:
            gs.upload(a, b, c, d)
            t0 = time.time()
            gs.thomas_solve()
            xs["thomas"] = gs.download(gs.xt)
            times["thomas"] = (t0, time.time())
            t0 = time.time()
            gs.pcr_solve()
            xs["pcr"] = gs.download(gs.xp)
            times["pcr"] = (t0, time.time())
            if cus:
                gs.cusparse_prepare()
                t0 = time.time()
                xs["cusparse"] = gs.cusparse_solve_copy()
                times["cusparse"] = (t0, time.time())
        finally:
            gs.free()
        t0 = time.time()
        xs["scipy"] = scipy_reference(a, b, c, d)
        times["scipy"] = (t0, time.time())
        res = {k: rel_residual_np(a, b, c, d, x) for k, x in xs.items()}
        lv = {"N": N, "ref_diff": rel_diff_np(xs["cusparse"], xs["scipy"]) if cus else None}
        for sname in ("thomas", "pcr"):
            lv[sname] = {"res": res[sname],
                         "diff_cusparse": rel_diff_np(xs[sname], xs["cusparse"]) if cus else None,
                         "diff_scipy": rel_diff_np(xs[sname], xs["scipy"])}
        levels.append(lv)
        for sname, x in xs.items():
            row = {"kind": "anchor", "solver": sname, "N": N, "seed": ANCHOR_SEED, "rel_residual": res[sname],
                   "x": x.tolist(), "x_fingerprint": fingerprint(x), "degenerate": detect_bad_vector(x[:4096]),
                   "t_start_utc": times[sname][0], "t_end_utc": times[sname][1]}
            if sname in ("thomas", "pcr"):
                row["diff_vs_cusparse"] = lv[sname]["diff_cusparse"]
                row["diff_vs_scipy"] = lv[sname]["diff_scipy"]
            elif sname == "cusparse":
                row["diff_vs_scipy"] = lv["ref_diff"]
            rows.write(row)
            rec_rows.append({k: v for k, v in row.items() if k != "x"})
    rows.close()
    sysrows.close()
    e1 = decide_e1(levels)
    apply_e1(out, e1)
    write_record(out, "E1", "endpoint",
                 ("anchor: relative residuals of Thomas and PCR at N = 2^10 and 2^14 (seed 0); relative "
                  "differences against cuSPARSE gtsv2_nopivot and scipy solve_banded; difference between the two "
                  "references"),
                 {"levels": levels, "solver_ok": e1["solver_ok"], "references_agree": e1["references_agree"],
                  "reasons": e1["reasons"]},
                 {"residual_max": RES_TOL, "difference_max_exclusive": DIFF_TOL}, RULES["E1"], e1["decision"],
                 rows=rec_rows, inputs=[describe_rows(out, "anchor")])
    all_res = [lv[s]["res"] for lv in levels for s in ("thomas", "pcr")]
    max_res = max(all_res) if all(math.isfinite(r) for r in all_res) else float("nan")
    e2 = decide_e2(max_res)
    write_record(out, "E2", "endpoint",
                 "card guess res_measured = 1e-13: measured max relative residual of Thomas and PCR at the anchor",
                 e2, {"band": list(E2_BAND), "guess": E2_GUESS}, RULES["E2"],
                 e2["decision"] + (f" ({e2['direction']})" if e2.get("direction") else ""),
                 inputs=[describe_rows(out, "anchor")])
    return EXIT_OK


def stage_timers(ctx: Ctx) -> int:
    out = ctx.out
    lib = Lib(ctx.so)
    rows, sysrows = Rows(out, "timers"), Rows(out, "systems_timers")
    t0 = time.perf_counter()
    time.sleep(TIMER_SLEEP_MS / 1000.0)
    sleep_ms = (time.perf_counter() - t0) * 1000.0
    rows.write({"kind": "timer", "check": "sleep", "requested_ms": TIMER_SLEEP_MS, "measured_ms": sleep_ms})
    N = TIMER_N
    a, b, c, d = make_system(N, 0)
    sysrows.write(system_row(N, 0, a, b, c, d, "timers"))
    gs = GpuSystem(lib, N, thomas=True, pcr=True)
    blocks, event_ms, wall_ms = {}, None, None
    try:
        gs.upload(a, b, c, d)
        for solver, fn in (("pcr", gs.pcr_block), ("thomas", gs.thomas_block)):
            warm = [fn(1) for _ in range(WARMUPS)]
            R = r_rule(warm[-1]) if pos_finite(warm[-1]) else 1
            w0 = time.perf_counter()
            bR = fn(R)
            w1 = time.perf_counter()
            b2R = fn(2 * R)
            if solver == "pcr":
                event_ms, wall_ms = bR, (w1 - w0) * 1000.0
            blocks[solver] = (R, bR, b2R)
            rows.write({"kind": "timer", "check": "block", "solver": solver, "N": N, "seed": 0, "warmup_ms": warm,
                        "R": R, "block_R_ms": bR, "block_2R_ms": b2R, "wall_ms_around_block_R": (w1 - w0) * 1e3})
    finally:
        gs.free()
    rows.close()
    sysrows.close()
    chk = check_timers(sleep_ms, event_ms, wall_ms, blocks)
    if not chk["ok"]:
        void(out, "timers", f"timer control out of tolerance: {json.dumps(chk)}")
    write_record(out, "timers", "control",
                 "timers: CPU sleep clock; cudaEvent against wall clock on one PCR block; 2R block against R",
                 {"checks": chk}, {"sleep_ms": [TIMER_SLEEP_MS, TIMER_SLEEP_TOL_MS], "event_rel": TIMER_EVENT_TOL,
                                   "two_r_rel": TIMER_2R_TOL}, RULES["timers"], "PASS" if chk["ok"] else "FAIL",
                 inputs=[describe_rows(out, "timers")])
    return EXIT_OK


def stage_residual_sweep(ctx: Ctx) -> int:
    out = ctx.out
    lib = Lib(ctx.so)
    rows, sysrows = Rows(out, "residual_sweep"), Rows(out, "systems_residual_sweep")
    per = []
    for N in LEVELS:
        gs = GpuSystem(lib, N, thomas=True, pcr=True)
        mx = {"thomas": 0.0, "pcr": 0.0}
        try:
            for seed in SEEDS:
                a, b, c, d = make_system(N, seed)
                sysrows.write(system_row(N, seed, a, b, c, d, "residual sweep"))
                gs.upload(a, b, c, d)
                gs.thomas_solve()
                xt = gs.download(gs.xt)
                gs.pcr_solve()
                xp = gs.download(gs.xp)
                dtp = rel_diff_np(xt, xp)
                for solver, x in (("thomas", xt), ("pcr", xp)):
                    r = rel_residual_np(a, b, c, d, x)
                    mx[solver] = max(mx[solver], r) if math.isfinite(r) else float("nan")
                    rows.write(dict({"kind": "residual", "solver": solver, "N": N, "seed": seed, "rel_residual": r,
                                     "diff_thomas_vs_pcr": dtp, "x_fingerprint": fingerprint(x)}, **vec_flags(x)))
                log(f"residual sweep N={N} seed={seed} done")
        finally:
            gs.free()
        per.append({"N": N, "max_rel_residual_thomas": mx["thomas"], "max_rel_residual_pcr": mx["pcr"]})
    rows.close()
    sysrows.close()
    write_record(out, "residual_sweep", "report",
                 "relative residual of one Thomas and one PCR solve at every sweep level and seed",
                 {"per_level": per}, {}, RULES["residual_sweep"], "REPORTED", role=ROLE_REPORT_ONLY,
                 inputs=[describe_rows(out, "residual_sweep")])
    return EXIT_OK


def write_arm_record(out: Path, arm: str, extra: dict | None = None) -> None:
    rows = read_rows(out, arm)
    tab = ms_table(rows)
    per = []
    for N in LEVELS:
        v = [tab.get(N, {}).get(s) for s in SEEDS]
        good = [x for x in v if pos_finite(x)]
        per.append({"N": N, "seeds_present": len(good), "median_ms_per_solve": median(good) if good else None,
                    "iqr_ms_per_solve": iqr(good) if len(good) >= 2 else None,
                    "R": [r.get("R") for r in rows if r.get("N") == N]})
    st = load_state(out)
    status = anchor_status(arm, st)
    decision = "MEASURED" if table_complete(tab) else "INCOMPLETE"
    if status == LABEL_ANCHOR_FAILED:
        decision += f"; {LABEL_ANCHOR_FAILED}"
    vals = {"arm": arm, "per_level": per, "anchor_status": status}
    vals.update(extra or {})
    write_record(out, arm, "arm", ARM_TEXT[arm], vals, {"seeds_per_level": len(SEEDS), "block_ms_at_least": BLOCK_MS},
                 RULES["arm"], decision, inputs=[describe_rows(out, arm)])


def fill_launch_fraction(out: Path) -> None:
    """Every PCR row gets launch_fraction = log2(N) x ms per launch / ms per solve, once the probe has run."""
    probe = ms_table(read_rows(out, "launch_probe"))
    per_level = {N: median(list(v.values())) for N, v in probe.items()
                 if all(pos_finite(v.get(s)) for s in SEEDS)}
    path = Path(out) / "rows" / "pcr_gpu.jsonl"
    if not path.exists():
        return
    rows = read_jsonl(path)
    for r in rows:
        m = per_level.get(int(r["N"]))
        if m is not None and pos_finite(r.get("ms_per_solve")):
            r["ms_per_launch"] = m
            r["launch_fraction"] = launch_fraction(int(r["N"]), m, r["ms_per_solve"])
            r["launch_fraction_from"] = "median ms per launch over the launch probe's five rows at this level"
    _atomic_write(path, "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))


def run_gpu_arm(ctx: Ctx, arm: str) -> int:
    out = ctx.out
    lib = Lib(ctx.so)
    st = load_state(out)
    if arm == "cusparse_gpu" and not (lib.has_cusparse and st.get("cusparse_available")):
        write_record(out, arm, "arm", ARM_TEXT[arm], {"arm": arm}, {}, RULES["arm"],
                     "NOT_RUN: cuSPARSE library missing at link or load time", inputs=code_inputs())
        return EXIT_OK
    rows, sysrows = Rows(out, arm, arm=arm), Rows(out, f"systems_{arm}")
    for N in LEVELS:
        K = k_rule(N) if arm == "thomas_batched_gpu" else 1
        gs = GpuSystem(lib, N, K=K, thomas=arm in ("thomas_gpu", "thomas_batched_gpu"), pcr=arm == "pcr_gpu")
        try:
            if arm == "cusparse_gpu":
                gs.cusparse_prepare()
            for seed in SEEDS:
                a, b, c, d = make_system(N, seed)
                sysrows.write(system_row(N, seed, a, b, c, d, arm))
                gs.upload(a, b, c, d)
                if arm in ("thomas_gpu", "thomas_batched_gpu"):
                    cell = time_cell(gs.thomas_block)
                    x = gs.download(gs.xt)
                elif arm == "pcr_gpu":
                    cell = time_cell(gs.pcr_block)
                    x = gs.download(gs.xp)
                else:
                    cell = time_cell(gs.cusparse_block)
                    x = gs.last_x
                row = {"kind": "timing", "arm": arm, "N": N, "seed": seed, "K": K}
                row.update(cell)
                row.update(vec_flags(x))
                if arm == "pcr_gpu":
                    row.update({"rounds": log2_int(N), "launches_per_solve": log2_int(N),
                                "grid": (N + PCR_BLOCKDIM - 1) // PCR_BLOCKDIM, "block_dim": PCR_BLOCKDIM,
                                "launch_fraction": None, "ms_per_launch": None})
                elif arm == "cusparse_gpu":
                    row.update({"copies_made": WARMUPS + cell["R"], "copies_in_timed_block": cell["R"],
                                "buffer_bytes": gs.sp_bytes,
                                "copy_rule": "one right-hand-side copy per solve, made before the timed block"})
                elif arm == "thomas_batched_gpu":
                    row.update({"layout": "K copies of the (N, seed) system laid out one after another",
                                "grid": K, "block_dim": 1, "x_checked": "first copy"})
                else:
                    row.update({"grid": 1, "block_dim": 1})
                rows.write(row)
                log(f"{arm} N={N} seed={seed} R={cell['R']} ms/solve={cell['ms_per_solve']:.6g}")
        finally:
            gs.free()
    rows.close()
    sysrows.close()
    write_arm_record(out, arm)
    return EXIT_OK


def stage_launch_probe(ctx: Ctx) -> int:
    out = ctx.out
    lib = Lib(ctx.so)
    rows = Rows(out, "launch_probe", arm="launch_probe")
    for N in LEVELS:
        grid = (N + PCR_BLOCKDIM - 1) // PCR_BLOCKDIM
        for seed in SEEDS:
            cell = time_cell(lambda R, g=grid: lib.time_empty(R, g, PCR_BLOCKDIM))
            row = {"kind": "timing", "arm": "launch_probe", "N": N, "seed": seed, "grid": grid,
                   "block_dim": PCR_BLOCKDIM, "ms_per_launch": cell["ms_per_solve"],
                   "note": "no system is solved; the seed index only repeats the protocol"}
            row.update(cell)
            rows.write(row)
            log(f"launch_probe N={N} seed={seed} R={cell['R']} ms/launch={cell['ms_per_solve']:.6g}")
    rows.close()
    fill_launch_fraction(out)
    write_arm_record(out, "launch_probe")
    return EXIT_OK


def stage_cpu_dgtsv(ctx: Ctx) -> int:
    out = ctx.out
    from scipy.linalg import lapack
    dgtsv = lapack.dgtsv
    rows, sysrows = Rows(out, "cpu_dgtsv", arm="cpu_dgtsv"), Rows(out, "systems_cpu_dgtsv")
    for N in LEVELS:
        for seed in SEEDS:
            a, b, c, d = make_system(N, seed)
            sysrows.write(system_row(N, seed, a, b, c, d, "cpu_dgtsv"))
            dl, dd, du, rhs = a[1:].copy(), b.copy(), c[:-1].copy(), d.copy()
            track = {"copies": 0, "info": 0, "x": None}

            def block(R, dl=dl, dd=dd, du=du, rhs=rhs, track=track):
                copies = [(dl.copy(), dd.copy(), du.copy(), rhs.copy()) for _ in range(R)]
                track["copies"] += R
                infos = [0] * R
                res = None
                t0 = time.perf_counter()
                for k in range(R):
                    cp = copies[k]
                    res = dgtsv(cp[0], cp[1], cp[2], cp[3], overwrite_dl=1, overwrite_d=1, overwrite_du=1,
                                overwrite_b=1)
                    infos[k] = res[4]
                t1 = time.perf_counter()
                track["info"] = max([track["info"]] + [abs(int(i)) for i in infos])
                track["x"] = res[3]
                return (t1 - t0) * 1000.0

            cell = time_cell(block)
            row = {"kind": "timing", "arm": "cpu_dgtsv", "N": N, "seed": seed, "copies_made": track["copies"],
                   "copies_in_timed_block": cell["R"], "solver_status": track["info"],
                   "copy_rule": "dgtsv overwrites its inputs; one input copy per call, made before the timed block",
                   "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                   "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                   "mkl_num_threads": os.environ.get("MKL_NUM_THREADS")}
            row.update(cell)
            row.update(vec_flags(track["x"]))
            rows.write(row)
            log(f"cpu_dgtsv N={N} seed={seed} R={cell['R']} ms/solve={cell['ms_per_solve']:.6g}")
    rows.close()
    sysrows.close()
    write_arm_record(out, "cpu_dgtsv")
    return EXIT_OK


# ------------------------------------------------------------------------------------------------------------
# Endpoints (stdlib only, so the selftest runs them on planted rows)
# ------------------------------------------------------------------------------------------------------------
def anchor_block_reason(st: dict) -> str | None:
    if not st.get("anchor_done"):
        return "NOT_READ: the anchor has not run"
    failed = [s for s in ("thomas", "pcr") if s in st.get("anchor_failed", [])]
    if failed:
        return f"NOT_READ: anchor failed for {' and '.join(failed)}"
    return None


def level_median(rows, key: str, N: int):
    vals = [r.get(key) for r in rows if r.get("kind") == "timing" and int(r["N"]) == N and pos_finite(r.get(key))]
    return median(vals) if vals else None


def compute_endpoints(out: Path) -> int:
    out = Path(out)
    rows = {arm: read_rows(out, arm) for arm in TIMING_ARMS}
    tabs = {arm: ms_table(rows[arm]) for arm in TIMING_ARMS}
    comp = {arm: table_complete(tabs[arm]) for arm in TIMING_ARMS}
    inputs = [describe_rows(out, arm) for arm in TIMING_ARMS]

    bad = []
    for arm in TIMING_ARMS:
        for r in rows[arm]:
            why = detect_bad_timing_row(r)
            if why:
                bad.append({"arm": arm, "N": r.get("N"), "seed": r.get("seed"), "why": why})
    if bad:
        void(out, "timing rows check", f"{len(bad)} degenerate timing rows")
    write_record(out, "timing_rows_check", "detector", "degenerate-output detector over every timing row",
                 {"degenerate_rows": bad, "complete": comp, "missing": {a: missing_cells(tabs[a]) for a in TIMING_ARMS}},
                 {}, RULES["timing_rows_check"], "PASS" if not bad else f"FAIL: {len(bad)} degenerate rows",
                 inputs=inputs)

    groups = []
    if comp["thomas_gpu"] and comp["pcr_gpu"]:
        groups.append(("Thomas ms / PCR ms", tabs["thomas_gpu"], tabs["pcr_gpu"]))
    if comp["cpu_dgtsv"] and comp["pcr_gpu"]:
        groups.append(("CPU dgtsv ms / PCR ms", tabs["cpu_dgtsv"], tabs["pcr_gpu"]))
    disp, zero = [], []
    for name, num, den in groups:
        for N in LEVELS:
            q = iqr([num[N][s] / den[N][s] for s in SEEDS])
            disp.append({"quantity": name, "N": N, "iqr": q})
            if q == 0.0:
                zero.append({"quantity": name, "N": N})
    if zero:
        void(out, "dispersion", f"zero dispersion over seeds: {zero}")
        write_record(out, "dispersion", "gate", "interquartile range over seeds of the noise-rule ratios",
                     {"per_level": disp, "zero": zero}, {"iqr_must_exceed": 0.0}, RULES["dispersion"],
                     "WRONG_VARIANCE_SOURCE", inputs=inputs)
        log("HALT WRONG_VARIANCE_SOURCE: endpoints not computed")
        return EXIT_WRONG_VARIANCE
    write_record(out, "dispersion", "gate", "interquartile range over seeds of the noise-rule ratios",
                 {"per_level": disp}, {"iqr_must_exceed": 0.0}, RULES["dispersion"],
                 "PASS" if groups else "NOT_RUN: rows incomplete", inputs=inputs)

    st = load_state(out)
    block = anchor_block_reason(st)
    lf = {N: level_median(rows["pcr_gpu"], "launch_fraction", N) for N in LEVELS}
    lf_report = {"launch_fraction_2e10": lf[LEVELS[0]], "launch_fraction_2e24": lf[LEVELS[-1]]}
    th_pcr = comp["thomas_gpu"] and comp["pcr_gpu"]
    lever = lever_from_tables(tabs["thomas_gpu"], tabs["pcr_gpu"]) if th_pcr else None
    incomplete = "NOT_RUN: Thomas or PCR timing rows incomplete"

    # E3: the card's decision.
    m3 = "card decision: median one-thread Thomas ms / median PCR ms against the card's rule"
    if block or not lever:
        write_record(out, "E3", "endpoint", m3, dict(lf_report, lever=lever), {"speedup_top_min": GATE_SPEEDUP},
                     RULES["E3"], block or incomplete, inputs=inputs)
    else:
        dec = lever["decision"] + (f" ({lever['label']})" if lever["label"] else "")
        write_record(out, "E3", "endpoint", m3, dict(lf_report, **lever), {"speedup_top_min": GATE_SPEEDUP},
                     RULES["E3"], dec, inputs=inputs)

    # E4: crossover.
    m4 = "card guess crossover_n = 1024: smallest level where the lower quartile of Thomas_ms / PCR_ms exceeds 1"
    if block or not lever:
        write_record(out, "E4", "endpoint", m4, dict(lf_report), {"crossover_must_be": LEVELS[0]}, RULES["E4"],
                     block or incomplete, inputs=inputs)
    else:
        e4 = decide_e4([r["lower_quartile_ratio"] for r in lever["table"]])
        lf10 = lf[LEVELS[0]]
        label = "crossover at 2^10 is launch-bound" if (lf10 is not None and lf10 > LAUNCH_BOUND) else None
        e4.update(lf_report, label=label)
        write_record(out, "E4", "endpoint", m4, e4, {"crossover_must_be": LEVELS[0], "launch_bound_above": LAUNCH_BOUND},
                     RULES["E4"], e4["decision"] + (f" ({label})" if label else ""), inputs=inputs)

    # E5: proxy 28.
    m5 = "card proxy speedup_at_nmax = 28: measured speedup at 2^24"
    if block or not lever:
        write_record(out, "E5", "endpoint", m5, {}, {"band": list(E5_BAND), "proxy": E5_PROXY}, RULES["E5"],
                     block or incomplete, inputs=inputs)
    else:
        e5 = decide_e5(lever["speedups"][-1])
        write_record(out, "E5", "endpoint", m5, e5, {"band": list(E5_BAND), "proxy": E5_PROXY}, RULES["E5"],
                     e5["decision"] + (f" ({e5['direction']}, measured / 28 = {e5['measured_over_proxy']:.4g})"
                                       if e5["direction"] else ""), inputs=inputs)

    pcr_label = {"pcr_anchor_status": anchor_status("pcr_gpu", st)}
    th_label = {"thomas_anchor_status": anchor_status("thomas_gpu", st)}

    # E6: PCR growth shape (report only).
    m6 = "shape of PCR time: g = (median PCR ms at 2^24 / median PCR ms at 2^22)^(1/2)"
    if comp["pcr_gpu"]:
        e6 = decide_e6(level_median(rows["pcr_gpu"], "ms_per_solve", 2 ** 22),
                       level_median(rows["pcr_gpu"], "ms_per_solve", 2 ** 24))
        e6.update(pcr_label)
        write_record(out, "E6", "endpoint", m6, e6, {"log_like_max": E6_LOG_MAX, "linear_like_min": E6_LIN_MIN},
                     RULES["E6"], e6["decision"], role=ROLE_REPORT_ONLY, inputs=inputs)
    else:
        write_record(out, "E6", "endpoint", m6, pcr_label, {}, RULES["E6"], "NOT_RUN: PCR rows incomplete",
                     role=ROLE_REPORT_ONLY, inputs=inputs)

    # E7: the card's rule against the CPU floor (report only).
    m7 = "CPU floor: the card's rule with median one-core scipy dgtsv ms in place of Thomas ms"
    if comp["cpu_dgtsv"] and comp["pcr_gpu"]:
        e7 = lever_from_tables(tabs["cpu_dgtsv"], tabs["pcr_gpu"])
        e7.update(pcr_label)
        write_record(out, "E7", "endpoint", m7, e7, {"speedup_top_min": GATE_SPEEDUP}, RULES["E7"],
                     e7["decision"] + " under the CPU baseline" + (f" ({e7['label']})" if e7["label"] else ""),
                     role=ROLE_REPORT_ONLY, inputs=inputs)
    else:
        write_record(out, "E7", "endpoint", m7, pcr_label, {}, RULES["E7"], "NOT_RUN: CPU or PCR rows incomplete",
                     role=ROLE_REPORT_ONLY, inputs=inputs)

    # E8: copies (report only).
    m8 = "copies: median batched Thomas ms / median single Thomas ms, and throughput factor K / ratio"
    if comp["thomas_batched_gpu"] and comp["thomas_gpu"]:
        ratios = [level_median(rows["thomas_batched_gpu"], "ms_per_solve", N) /
                  level_median(rows["thomas_gpu"], "ms_per_solve", N) for N in LEVELS]
        e8 = decide_e8(ratios, [k_rule(N) for N in LEVELS])
        e8.update(th_label)
        write_record(out, "E8", "endpoint", m8, e8, {"band": list(E8_BAND)}, RULES["E8"],
                     e8["decision"] + (f" ({e8['label']})" if e8["label"] else ""), role=ROLE_REPORT_ONLY,
                     inputs=inputs)
    else:
        write_record(out, "E8", "endpoint", m8, th_label, {}, RULES["E8"], "NOT_RUN: Thomas rows incomplete",
                     role=ROLE_REPORT_ONLY, inputs=inputs)

    # E9: cuSPARSE against PCR (report only).
    m9 = "cuSPARSE: median gtsv2_nopivot ms at each level and median PCR ms / median cuSPARSE ms"
    if st.get("cusparse_available") is False:
        write_record(out, "E9", "endpoint", m9, {}, {}, RULES["E9"],
                     "NOT_RUN: cuSPARSE library missing at link or load time", role=ROLE_REPORT_ONLY, inputs=inputs)
    elif comp["cusparse_gpu"] and comp["pcr_gpu"]:
        e9 = decide_e9([level_median(rows["cusparse_gpu"], "ms_per_solve", N) for N in LEVELS],
                       [level_median(rows["pcr_gpu"], "ms_per_solve", N) for N in LEVELS])
        e9.update(pcr_label, levels=LEVELS)
        write_record(out, "E9", "endpoint", m9, e9, {}, RULES["E9"], "REPORTED", role=ROLE_REPORT_ONLY,
                     inputs=inputs)
    else:
        write_record(out, "E9", "endpoint", m9, {}, {}, RULES["E9"], "NOT_RUN: cuSPARSE or PCR rows incomplete",
                     role=ROLE_REPORT_ONLY, inputs=inputs)

    # E10: hours from the first anchor solve to the last sweep row.
    m10 = "card cost line 'need 2 h': hours from the first anchor solve to the last sweep row"
    starts = [r["t_start_utc"] for r in read_rows(out, "anchor") if is_num(r.get("t_start_utc"))]
    ends = [r["t_written_utc"] for name in SWEEP_ROW_FILES for r in read_rows(out, name)
            if is_num(r.get("t_written_utc"))]
    if starts and ends:
        t_first, t_last = min(starts), max(ends)
        e10 = decide_e10((t_last - t_first) / 3600.0)
        e10.update({"first_anchor_solve_utc": t_first, "last_sweep_row_utc": t_last, "card_need_hours": E10_NEED_H})
        write_record(out, "E10", "endpoint", m10, e10, {"band_hours": list(E10_BAND)}, RULES["E10"],
                     e10["decision"] + (f" ({e10['direction']})" if e10["direction"] else ""),
                     inputs=[describe_rows(out, "anchor")] + [describe_rows(out, n) for n in SWEEP_ROW_FILES])
    else:
        write_record(out, "E10", "endpoint", m10, {}, {"band_hours": list(E10_BAND)}, RULES["E10"],
                     "NOT_RUN: anchor or sweep timestamps missing", inputs=inputs)
    return EXIT_OK


def stage_endpoints(ctx: Ctx) -> int:
    return compute_endpoints(ctx.out)


def write_summary(out: Path, exit_code: int, stop_reason: str) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if not state_path(out).exists():
        init_state(out)
        void(out, "summary", "no stage wrote the run-validity file, so nothing was measured")
    st = load_state(out)
    decisions, unreadable = {}, []
    for p in sorted((out / "records").glob("*.json")) if (out / "records").exists() else []:
        try:
            r = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            unreadable.append(p.name)
            continue
        decisions[r["cell"]["id"]] = {"kind": r["cell"]["kind"], "decision": r.get("decision"),
                                      "run_valid": r.get("values", {}).get("run_valid"),
                                      "role": r.get("values", {}).get("role"), "file": f"records/{p.name}"}
    stages = read_jsonl(out / "stages.jsonl") if (out / "stages.jsonl").exists() else []
    summary = {"run": TAG, "run_valid": st["run_valid"], "voids": st["voids"], "anchor_failed": st["anchor_failed"],
               "one_reference_only": st["one_reference_only"], "cusparse_available": st.get("cusparse_available"),
               "labels": full_labels(out), "exit_code": exit_code, "stop_reason": stop_reason, "stages": stages,
               "decisions": decisions, "records_missing": [k for k in EXPECTED_RECORDS if k not in decisions],
               "records_unreadable": unreadable, "note": SUMMARY_NOTE, "written_utc": time.time()}
    _atomic_write(out / "m2_summary.json", json.dumps(summary, indent=2, sort_keys=True))
    log(f"summary written: run_valid={st['run_valid']} exit_code={exit_code} ({stop_reason})")
    return summary


# ------------------------------------------------------------------------------------------------------------
# Planted controls I2..I10 (execution note item 8) and gate propagation (item 10)
# ------------------------------------------------------------------------------------------------------------
def per_seed(values_by_level, overrides: dict | None = None) -> dict:
    """Planted {N: {seed: ms}}: every seed gets the level's value unless overridden."""
    t = {N: {s: float(v) for s in SEEDS} for N, v in zip(LEVELS, values_by_level)}
    for N, vals in (overrides or {}).items():
        t[N] = {s: float(v) for s, v in zip(SEEDS, vals)}
    return t


def planted_controls() -> list:
    out = []

    def ctl(cid, metric, cases, threshold):
        out.append({"id": cid, "metric": metric, "values": {"cases": cases}, "threshold": threshold,
                    "rule": RULES["planted"], "ok": all(c["ok"] for c in cases)})

    cases = []
    for planted, want, direction in ((1e-13, "HOLDS", None), (5e-15, "REFUTED", "too pessimistic"),
                                     (5e-12, "REFUTED", "too optimistic")):
        r = decide_e2(planted)
        cases.append({"planted": planted, "want": [want, direction], "got": [r["decision"], r["direction"]],
                      "ok": r["decision"] == want and r["direction"] == direction})
    ctl("I2", "planted arithmetic for E2 (residual guess band)", cases, {"band": list(E2_BAND)})

    cases = []
    th, pcr = [1, 16, 256, 4096, 16384], [0.5, 0.6, 1, 10, 40]
    want_s = [2, 26.667, 256, 409.6, 409.6]
    r = lever_from_tables(per_seed(th), per_seed(pcr))
    cases.append({"case": "growing speedups", "want": [want_s, "if_lever", "slope > 0"],
                  "got": [r["speedups"], r["decision"], r["slope_ln_speedup_per_log2N"]],
                  "ok": all(same4(g, w) for g, w in zip(r["speedups"], want_s))
                  and r["slope_ln_speedup_per_log2N"] > 0 and r["decision"] == "if_lever" and r["label"] is None})
    r = lever_from_tables(per_seed([5, 10, 20, 40, 80]), per_seed([1, 2, 4, 8, 16]))
    cases.append({"case": "equal speedups", "want": "if_not", "got": [r["speedups"], r["decision"]],
                  "ok": r["decision"] == "if_not"})
    r = lever_from_tables(per_seed([1, 1.2, 1.4, 1.6, 1.9]), per_seed([1] * 5))
    cases.append({"case": "speedup(2^24) = 1.9", "want": "if_not", "got": [r["speedups"][-1], r["decision"]],
                  "ok": same4(r["speedups"][-1], 1.9) and r["decision"] == "if_not"})
    r = lever_from_tables(per_seed([1, 1.5, 2, 2.5, 3], {2 ** 24: [1.8, 1.8, 3, 4, 5]}), per_seed([1] * 5))
    cases.append({"case": "lower quartile 1.8, median 3 at 2^24", "want": ["if_lever", "within noise"],
                  "got": [r["speedups"][-1], r["lower_quartile_top"], r["decision"], r["label"]],
                  "ok": same4(r["speedups"][-1], 3) and same4(r["lower_quartile_top"], 1.8)
                  and r["decision"] == "if_lever" and r["label"] == "within noise"})
    ctl("I3", "planted arithmetic for E3 (the card's decision rule)", cases, {"speedup_top_min": GATE_SPEEDUP})

    cases = []
    for lqs, want_n, want in (([1.2, 3, 10, 50, 100], 2 ** 10, "HOLDS"), ([0.8, 1.5, 10, 50, 100], 2 ** 14, "REFUTED"),
                              ([0.5, 0.6, 0.7, 0.8, 0.9], None, "REFUTED")):
        r = decide_e4(lqs)
        cases.append({"planted_lower_quartiles": lqs, "want": [want_n, want], "got": [r["crossover_N"], r["decision"]],
                      "ok": r["crossover_N"] == want_n and r["decision"] == want})
    ctl("I4", "planted arithmetic for E4 (crossover level)", cases, {"crossover_must_be": LEVELS[0]})

    cases = []
    for s_top, want, direction, ratio in ((28, "HOLDS", None, 1.0), (100, "REFUTED", "above", 3.571),
                                          (5, "REFUTED", "below", 5 / 28)):
        r = decide_e5(s_top)
        cases.append({"planted": s_top, "want": [want, direction, ratio],
                      "got": [r["decision"], r["direction"], r["measured_over_proxy"]],
                      "ok": r["decision"] == want and r["direction"] == direction
                      and same4(r["measured_over_proxy"], ratio)})
    ctl("I5", "planted arithmetic for E5 (proxy 28)", cases, {"band": list(E5_BAND)})

    cases = []
    for m22, m24, g, shape in ((10, 11, 1.0488, "log-like"), (10, 40, 2, "linear-like"), (10, 20, 1.4142, "between")):
        r = decide_e6(m22, m24)
        cases.append({"planted": [m22, m24], "want": [g, shape], "got": [r["g"], r["decision"]],
                      "ok": same4(r["g"], g) and r["decision"] == shape})
    ctl("I6", "planted arithmetic for E6 (growth shape)", cases, {"log_like_max": E6_LOG_MAX,
                                                                  "linear_like_min": E6_LIN_MIN})

    cases = []
    cpu = [0.01, 0.1, 2, 40, 160]
    r = lever_from_tables(per_seed(cpu), per_seed(pcr))
    cases.append({"case": "CPU floor lever", "want": [4, "if_lever"], "got": [r["speedups"][-1], r["decision"]],
                  "ok": same4(r["speedups"][-1], 4) and r["decision"] == "if_lever"})
    r = lever_from_tables(per_seed(cpu[:4] + [60]), per_seed(pcr))
    cases.append({"case": "CPU 60 ms at 2^24", "want": [1.5, "if_not"], "got": [r["speedups"][-1], r["decision"]],
                  "ok": same4(r["speedups"][-1], 1.5) and r["decision"] == "if_not"})
    ctl("I7", "planted arithmetic for E7 (CPU floor)", cases, {"speedup_top_min": GATE_SPEEDUP})

    cases = []
    ks = [k_rule(N) for N in LEVELS]
    for ratios, want in (([1.0, 1.1, 1.5, 2.9, 1.2], "HOLDS"), ([1.0, 3.5, 1.5, 2.9, 1.2], "FAILS")):
        r = decide_e8(ratios, ks)
        exact = all(t == k / q for t, k, q in zip(r["throughput_factor"], ks, ratios))
        cases.append({"planted_ratios": ratios, "K": ks, "want": want, "got": [r["decision"], r["throughput_factor"]],
                      "ok": r["decision"] == want and exact and ks == [256, 256, 256, 64, 16]})
    ctl("I8", "planted arithmetic for E8 (copies)", cases, {"band": list(E8_BAND)})

    r = decide_e9([10.0], [30.0])
    ctl("I9", "planted arithmetic for E9 (cuSPARSE ratio)",
        [{"planted": {"cusparse_ms": 10, "pcr_ms": 30}, "want": 3, "got": r["pcr_over_cusparse"][0],
          "ok": r["pcr_over_cusparse"][0] == 3.0}], {})

    cases = []
    for hours, want, below in ((0.5, "REFUTED", True), (2, "HOLDS", None), (7, "REFUTED", False)):
        r = decide_e10(hours)
        dir_ok = (r["direction"] is None) if below is None else (r["direction"].startswith("below" if below else "above"))
        cases.append({"planted_hours": hours, "want": want, "got": [r["decision"], r["direction"]],
                      "ok": r["decision"] == want and dir_ok})
    ctl("I10", "planted arithmetic for E10 (cost line hours)", cases, {"band_hours": list(E10_BAND)})
    return out


PLANTED_T0 = 1.7e9
JIT_F = [0.98, 0.99, 1.0, 1.01, 1.03]     # planted per-seed factors, median 1.0 each
JIT_G = [1.0, 1.02, 0.97, 1.01, 0.99]
JIT_H = [1.01, 0.99, 1.0, 1.02, 0.98]


def planted_env(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _atomic_write(out / "env.json", json.dumps({"instance_type": "planted (selftest)", "price_usd_per_hour": 1.99,
                                                "cusparse_available": True}, sort_keys=True))


def planted_anchor(thomas_res=1e-16, pcr_res=1e-16, ref_diff=1e-16, cusparse=True) -> list:
    return [{"N": N, "ref_diff": ref_diff if cusparse else None,
             "thomas": {"res": thomas_res, "diff_cusparse": 1e-15 if cusparse else None, "diff_scipy": 1e-15},
             "pcr": {"res": pcr_res, "diff_cusparse": 1e-15 if cusparse else None, "diff_scipy": 1e-15}}
            for N in ANCHOR_LEVELS]


def planted_tables(zero_level: int | None = None) -> dict:
    th, pcr, cpu = [1, 16, 256, 4096, 16384], [0.5, 0.6, 1, 10, 40], [0.01, 0.1, 2, 40, 160]
    bat = [1.0, 1.1, 1.5, 2.9, 1.2]
    t = {"thomas_gpu": {N: {s: v * JIT_F[s] for s in SEEDS} for N, v in zip(LEVELS, th)},
         "pcr_gpu": {N: {s: v * (JIT_F[s] if N == zero_level else JIT_G[s]) for s in SEEDS}
                     for N, v in zip(LEVELS, pcr)},
         "cpu_dgtsv": {N: {s: v * JIT_H[s] for s in SEEDS} for N, v in zip(LEVELS, cpu)},
         "thomas_batched_gpu": {N: {s: v * q * JIT_F[s] for s in SEEDS} for N, v, q in zip(LEVELS, th, bat)},
         "cusparse_gpu": {N: {s: v / 3.0 * JIT_G[s] for s in SEEDS} for N, v in zip(LEVELS, pcr)},
         "launch_probe": {N: {s: 0.004 for s in SEEDS} for N in LEVELS}}
    return t


def write_planted_rows(out: Path, tables: dict, hours: float = 2.0) -> None:
    """Planted rows through the same writers the box uses; the last sweep row lands `hours` after the anchor."""
    r = Rows(out, "anchor")
    r.write({"kind": "anchor", "solver": "thomas", "N": ANCHOR_LEVELS[0], "seed": 0, "t_start_utc": PLANTED_T0},
            t=PLANTED_T0)
    r.close()
    total = len(TIMING_ARMS) * len(LEVELS) * len(SEEDS)
    k = 0
    for arm in TIMING_ARMS:
        w = Rows(out, arm, arm=arm)
        for N in LEVELS:
            for s in SEEDS:
                k += 1
                ms = tables[arm][N][s]
                row = {"kind": "timing", "arm": arm, "N": N, "seed": s, "R": 1, "block_ms": ms, "ms_per_solve": ms,
                       "x_finite": True, "K": k_rule(N) if arm == "thomas_batched_gpu" else 1}
                if arm == "pcr_gpu":
                    row["launch_fraction"] = None
                w.write(row, t=PLANTED_T0 + hours * 3600.0 * k / total)
        w.close()
    fill_launch_fraction(out)


def planted_gate_propagation(tmp: Path):
    _LOG_TAG[0] = "(planted control, temporary directory) "
    try:
        return _planted_gate_propagation(Path(tmp))
    finally:
        _LOG_TAG[0] = ""


def _planted_gate_propagation(tmp: Path):
    details, ok = [], True

    def need(cond, what):
        nonlocal ok
        details.append({"check": what, "ok": bool(cond)})
        ok = ok and bool(cond)

    outA = tmp / "thomas_anchor_failure"
    planted_env(outA)
    init_state(outA)
    e1 = decide_e1(planted_anchor(thomas_res=1e-9))
    apply_e1(outA, e1)
    write_record(outA, "E1", "endpoint", "planted anchor", {"levels": "planted"}, {}, RULES["E1"], e1["decision"])
    write_planted_rows(outA, planted_tables())
    rc = compute_endpoints(outA)
    recs = read_records(outA)
    need(rc == EXIT_OK, "Thomas failure: endpoints stage completes")
    need(e1["solver_ok"] == {"thomas": False, "pcr": True}, "Thomas residual 1e-9 fails the anchor, PCR passes")
    th_rows = read_rows(outA, "thomas_gpu") + read_rows(outA, "thomas_batched_gpu")
    need(th_rows and all(r["anchor_status"] == LABEL_ANCHOR_FAILED for r in th_rows),
         "every Thomas timing row is labelled 'descriptive only; anchor failed'")
    need(all(r["anchor_status"] == "anchor passed" for r in read_rows(outA, "pcr_gpu")),
         "PCR rows are labelled 'anchor passed'")
    need(all(recs[k]["decision"].startswith("NOT_READ") for k in ("E3", "E4", "E5")), "E3, E4, E5 are NOT_READ")
    need(all(not recs[k]["decision"].startswith("NOT_READ") for k in ("E6", "E7", "E8", "E9", "E10")),
         "report-only readings E6..E10 are still computed")
    need(all(recs[k]["values"]["anchor_failed"] == ["thomas"] for k in recs if k != "E1"),
         "every later record carries the anchor failure")
    need(load_state(outA)["run_valid"] is (not ANCHOR_FAIL_VOIDS_RUN),
         "run_valid follows the execution note (an anchor failure alone does not void)")

    outB = tmp / "reference_disagreement"
    planted_env(outB)
    init_state(outB)
    write_record(outB, "before_gate", "control", "a record written before the gate", {}, {}, "planted", "PASS")
    rb = Rows(outB, "before_gate")
    rb.write({"kind": "planted"})
    rb.close()
    e1 = decide_e1(planted_anchor(ref_diff=1e-7))
    apply_e1(outB, e1)
    write_record(outB, "E1", "endpoint", "planted anchor", {"levels": "planted"}, {}, RULES["E1"], e1["decision"])
    write_planted_rows(outB, planted_tables())
    compute_endpoints(outB)
    summ = write_summary(outB, 0, "planted")
    recs = read_records(outB)
    need(e1["references_agree"] is False and e1["decision"].startswith("FAIL"), "references at 1e-7 fail E1")
    need(recs["before_gate"]["values"]["run_valid"] is True, "the record written before the gate keeps run_valid true")
    need(read_rows(outB, "before_gate")[0]["run_valid"] is True, "the row written before the gate keeps run_valid true")
    after = [k for k in recs if k != "before_gate"]
    need(len(after) >= 11 and all(recs[k]["values"]["run_valid"] is False for k in after),
         "every record written after the gate has run_valid false")
    rows_after = [r for name in ["anchor"] + TIMING_ARMS for r in read_rows(outB, name)]
    need(rows_after and all(r["run_valid"] is False for r in rows_after),
         "every row written after the gate has run_valid false, per-arm files included")
    need(summ["run_valid"] is False, "the summary restates run_valid false")
    return ok, details


# ------------------------------------------------------------------------------------------------------------
# Selftest (stdlib only)
# ------------------------------------------------------------------------------------------------------------
def selftest() -> int:
    before = set(sys.modules)
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond)))
        print(("ok    " if cond else "FAIL  ") + name + ("" if cond or not detail else f"  -- {detail}"), flush=True)

    def group(fn):
        try:
            fn()
        except Exception:  # noqa: BLE001
            check(f"{fn.__name__} ran without an exception", False, traceback.format_exc())

    tmp = Path(tempfile.mkdtemp(prefix="m2_selftest_"))

    def parsers():
        nv = ("nvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2025 NVIDIA Corporation\n"
              "Cuda compilation tools, release 12.8, V12.8.93\nBuild cuda_12.8.r12.8/compiler.35583870_0\n")
        check("parse_nvcc_version reads release and build", parse_nvcc_version(nv) == "12.8 (V12.8.93)",
              parse_nvcc_version(nv))
        check("parse_nvcc_version returns None on other text", parse_nvcc_version("command not found") is None)
        smi = parse_nvidia_smi_csv("NVIDIA A100-SXM4-40GB, 570.148.08, 40960 MiB\n")
        check("parse_nvidia_smi_csv reads name, driver, memory",
              smi == {"gpu_name": "NVIDIA A100-SXM4-40GB", "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB"}, smi)
        check("parse_nvidia_smi_csv gives unknowns on empty output", parse_nvidia_smi_csv("")["gpu_name"] is None)
        check("format_cuda_version 12080 -> 12.8; 11040 -> 11.4; 0 -> None",
              format_cuda_version(12080) == "12.8" and format_cuda_version(11040) == "11.4"
              and format_cuda_version(0) is None)
        cfg18 = ("lapack_mkl_info:\n  NOT AVAILABLE\nopenblas_lapack_info:\n  NOT AVAILABLE\n"
                 "lapack_opt_info:\n    libraries = ['lapack', 'lapack', 'blas', 'blas']\n"
                 "    library_dirs = ['/usr/lib/x86_64-linux-gnu']\n"
                 "    define_macros = [('NO_ATLAS_INFO', 1), ('HAVE_CBLAS', None)]\n")
        cfg_ob = ("blas_mkl_info:\n  NOT AVAILABLE\nopenblas_info:\n    libraries = ['openblas', 'openblas']\n"
                  "    library_dirs = ['/usr/local/lib']\n")
        cfg_new = ("Build Dependencies:\n  blas:\n    detection method: pkgconfig\n    found: true\n"
                   "    name: scipy-openblas\n  lapack:\n    name: scipy-openblas\n")
        check("parse_blas_vendor: old style, skips NOT AVAILABLE sections", parse_blas_vendor(cfg_ob) == "openblas",
              parse_blas_vendor(cfg_ob))
        check("parse_blas_vendor: mkl", parse_blas_vendor("blas_mkl_info:\n    libraries = ['mkl_rt']\n") == "mkl")
        check("parse_blas_vendor: generic names flagged as unnamed, macros ignored",
              parse_blas_vendor(cfg18).startswith("unnamed"), parse_blas_vendor(cfg18))
        check("parse_blas_vendor: new style reads the blas name", parse_blas_vendor(cfg_new) == "scipy-openblas",
              parse_blas_vendor(cfg_new))
        check("parse_blas_vendor: unknown", parse_blas_vendor("") == "unknown")
        ldd = ("\tlinux-vdso.so.1 (0x00007ffd)\n\tlibcusparse.so.12 => /usr/lib/x86_64-linux-gnu/libcusparse.so.12 "
               "(0x00007f)\n\tlibcudart.so.12 => not found\n")
        pl = parse_ldd(ldd)
        check("parse_ldd reads resolved and missing libraries",
              pl == {"libcusparse.so.12": "/usr/lib/x86_64-linux-gnu/libcusparse.so.12", "libcudart.so.12": None}, pl)
        check("parse_uptime reads the first field", parse_uptime("12345.67 23456.78\n") == 12345.67
              and parse_uptime("") is None)
        check("parse_positive_float accepts 1.99, rejects '', 'abc', '-1', 'nan'",
              parse_positive_float("1.99") == 1.99 and all(parse_positive_float(v) is None
                                                          for v in ("", "abc", "-1", "nan", None)))
        check("parse_nonneg_float accepts 0 and 6", parse_nonneg_float("0") == 0.0 and parse_nonneg_float("6") == 6.0)
        check("detect_cusparse_missing on link and header errors",
              detect_cusparse_missing("/usr/bin/ld: cannot find -lcusparse: No such file or directory")
              and detect_cusparse_missing("fatal error: cusparse.h: No such file or directory")
              and detect_cusparse_missing("OSError: libcusparse.so.12: cannot open shared object file"))
        check("detect_cusparse_missing ignores other compile errors",
              not detect_cusparse_missing("error: identifier \"foo\" is undefined"))
        check("cuda_dir_version_key orders cuda-12.10 above cuda-12.8",
              sorted(["/usr/local/cuda-12.10/bin/nvcc", "/usr/local/cuda-12.8/bin/nvcc"], key=cuda_dir_version_key)[-1]
              == "/usr/local/cuda-12.10/bin/nvcc")
        p = tmp / "rows.jsonl"
        p.write_text('{"a": 1}\n\n{"a": 2}\n')
        check("read_jsonl skips blank lines", read_jsonl(p) == [{"a": 1}, {"a": 2}])
        p.write_text('{"a": 1}\n{"a": \n')
        try:
            read_jsonl(p)
            check("read_jsonl rejects a malformed row", False)
        except ValueError:
            check("read_jsonl rejects a malformed row", True)

    def source_and_command():
        src = CUDA_SOURCE
        missing = [s for s in CUDA_EXPORTS + CUSPARSE_EXPORTS if not re.search(r"\b" + s + r"\s*\(", src)]
        check("CUDA source defines every function the bindings use", not missing, str(missing))
        check("CUDA source calls cusparseDgtsv2_nopivot_bufferSizeExt then cusparseDgtsv2_nopivot",
              "cusparseDgtsv2_nopivot_bufferSizeExt(m2_sparse, m, 1," in src and "cusparseDgtsv2_nopivot(m2_sparse, m, 1," in src)
        code = re.sub(r"//[^\n]*", "", src)
        check("CUDA source braces and parentheses balance (comments stripped)",
              code.count("{") == code.count("}") and code.count("(") == code.count(")"))
        check("Thomas launches one block of one thread per system (<<<K, 1>>>)", src.count("<<<K, 1>>>") == 2)
        check("PCR launches blocks of 256 threads, one launch per round",
              "#define M2_PCR_BLOCK 256" in src and "m2_pcr_round<<<grid, M2_PCR_BLOCK>>>" in src)
        check("no unroll pragma in the plain Thomas kernel", "#pragma unroll" not in src)
        want = ["nvcc", "-O3", "-shared", "-Xcompiler", "-fPIC", "-o", "results_m2/build/libm2.so",
                "results_m2/build/m2_kernels.cu", "-lcusparse", "-lcudart"]
        got = nvcc_command("nvcc", "results_m2/build/m2_kernels.cu", "results_m2/build/libm2.so", None, True)
        check("compile command is the execution note's, verbatim", got == want, str(got))
        got = nvcc_command("nvcc", "results_m2/build/m2_kernels.cu", "results_m2/build/libm2.so", "sm_80", True)
        check("A100 adds -arch=sm_80 only", got == want + ["-arch=sm_80"], str(got))
        got = nvcc_command("nvcc", "k.cu", "l.so", None, False)
        check("no-cuSPARSE rebuild drops -lcusparse and defines M2_NO_CUSPARSE",
              "-lcusparse" not in got and "-DM2_NO_CUSPARSE" in got and got[-1] == "-lcudart", str(got))

    def numerics():
        rng = random.Random(20261020)
        n = 16
        a = [0.0] + [rng.choice((-1.0, 1.0)) for _ in range(n - 1)]
        c = [rng.choice((-1.0, 1.0)) for _ in range(n - 1)] + [0.0]
        b = [B_DIAG] * n
        d = [rng.gauss(0.0, 1.0) for _ in range(n)]
        xt = thomas_py(a, b, c, d)
        rt = rel_residual_py(a, b, c, d, xt)
        check("pure Thomas on a 16-equation planted system: residual <= 1e-14", rt <= 1e-14, fmt(rt))
        xp, rounds = pcr_py(a, b, c, d)
        rp = rel_residual_py(a, b, c, d, xp)
        check("pure PCR mirror: log2(16) = 4 rounds and residual <= 1e-14", rounds == 4 and rp <= 1e-14,
              f"{rounds} {fmt(rp)}")
        check("pure Thomas and PCR agree to < 1e-12", rel_diff_py(xt, xp) < 1e-12, fmt(rel_diff_py(xt, xp)))
        xs = [1.0] * n
        ds = matvec_py(a, b, c, xs)
        r_exact = rel_residual_py(a, b, c, ds, xs)
        sg = alternating_signs(n)
        scale = norm_py(xs) / norm_py(sg)
        xpert = [x + I1_PERTURB * s * scale for x, s in zip(xs, sg)]
        r_pert = rel_residual_py(a, b, c, ds, xpert)
        i1 = decide_i1(r_exact, r_pert, 1e-16)
        check("readout control: exact x* reads <= 1e-14", i1["exact_ok"], fmt(r_exact))
        check("readout control: x* perturbed by 1e-6 reads inside [1e-7, 1e-5]", i1["perturbed_ok"], fmt(r_pert))
        check("perturbation is exactly 1e-6 relative", same4(rel_diff_py(xpert, xs), 1e-6))
        check("readout control fails a planted bad readout", not decide_i1(1e-12, 1e-3, 1e-7)["exact_ok"]
              and not decide_i1(0.0, 1e-3, None)["perturbed_ok"] and decide_i1(0, 1e-6, 1e-7)["references_ok"] is False)
        check("Thomas on d = A x* recovers x*", rel_diff_py(thomas_py(a, b, c, ds), xs) < 1e-14)
        wrong = [v * 1.001 for v in xt]
        check("a wrong solution reads above the anchor tolerance", rel_residual_py(a, b, c, d, wrong) > RES_TOL)
        fp = fingerprint([1.0, 2.0])
        check("fingerprint hashes float64 little-endian bytes",
              fp["sha256"] == hashlib.sha256(struct.pack("<2d", 1.0, 2.0)).hexdigest() and fp["first8"] == [1.0, 2.0])

    def rules_and_stats():
        check("R rule: 10 ms -> 5; 0.04 ms -> 1250; 50 ms -> 1; 60 ms -> 1",
              [r_rule(10), r_rule(0.04), r_rule(50), r_rule(60)] == [5, 1250, 1, 1])
        check("K rule over the levels is 256, 256, 256, 64, 16", [k_rule(N) for N in LEVELS] == [256, 256, 256, 64, 16])
        check("launch fraction: 10 x 0.004 / 0.05 = 0.8", same4(launch_fraction(2 ** 10, 0.004, 0.05), 0.8))
        xs = [5.0, 1.0, 4.0, 2.0, 3.0]
        check("median, lower quartile, upper quartile of 1..5 are 3, 2, 4",
              median(xs) == 3 and quantile(xs, 0.25) == 2 and quantile(xs, 0.75) == 4 and iqr(xs) == 2)
        check("least-squares slope of y = 2x + 1 is 2", same4(ls_slope([10, 14, 18, 22, 24], [21, 29, 37, 45, 49]), 2))
        t = check_timers(100.4, 50.0, 51.0, {"thomas": (8, 50.0, 101.0), "pcr": (700, 50.0, 99.0)})
        check("timers pass: sleep 100.4 ms, event 50 vs wall 51, 2R ratios 2.02 and 1.98", t["ok"], json.dumps(t))
        t = check_timers(106.0, 50.0, 51.0, {"thomas": (8, 50.0, 101.0)})
        check("timers fail: sleep 106 ms", not t["ok"] and not t["sleep_ok"])
        t = check_timers(100.0, 50.0, 55.0, {"thomas": (8, 50.0, 101.0)})
        check("timers fail: event 50 against wall 55 (9.1%)", not t["ok"] and not t["event_ok"])
        t = check_timers(100.0, 50.0, 50.5, {"pcr": (8, 50.0, 125.0)})
        check("timers fail: 2R block 2.5x the R block", not t["ok"] and not t["two_r"]["pcr"]["ok"])
        g = guard_decision(3600, 100, 400, 1.99, 6)
        check("guard: early in the run allows the time left minus the reserve", g == ("RUN", 3410), str(g))
        g = guard_decision(3600, 3500, 3800, 1.99, 6)
        check("guard: time guard stops near REMOTE_TIMEOUT", g[0] == "STOP" and g[1].startswith("time guard"), str(g))
        g = guard_decision(3600, 100, 400, 1.99, 0.3)
        check("guard: cost guard stops when the budget is nearly spent",
              g[0] == "STOP" and g[1].startswith("cost guard"), str(g))

    def detectors():
        check("bad vector: non-finite", detect_bad_vector([1.0, float("nan")]) == "non-finite values")
        check("bad vector: all zeros", detect_bad_vector([0.0, 0.0]) == "all zeros")
        check("bad vector: empty", detect_bad_vector([]) == "empty")
        check("good vector passes", detect_bad_vector([1.0, -2.0]) is None)
        good = {"kind": "timing", "ms_per_solve": 1.0, "block_ms": 50.0, "R": 50, "x_finite": True}
        check("good timing row passes", detect_bad_timing_row(good) is None)
        for bad, what in ((dict(good, ms_per_solve=0.0), "zero ms"), (dict(good, block_ms=float("nan")), "nan block"),
                          (dict(good, ms_per_solve=-1.0), "negative ms"), (dict(good, R=0), "R = 0"),
                          (dict(good, x_finite=False), "non-finite solution"), (dict(good, solver_status=3), "status 3"),
                          (dict(good, degenerate="second warm-up ms not positive"), "degenerate warm-up")):
            check(f"bad timing row caught: {what}", detect_bad_timing_row(bad) is not None)
        t = {N: {s: 1.0 for s in SEEDS} for N in LEVELS}
        check("complete table passes", table_complete(t) and missing_cells(t) == [])
        t[2 ** 24].pop(4)
        check("missing seed makes the table incomplete", not table_complete(t) and missing_cells(t) == [[2 ** 24, 4]])

    def e1_decisions():
        e = decide_e1(planted_anchor())
        check("E1 passes a clean planted anchor", e["decision"] == "PASS" and e["references_agree"] is True)
        e = decide_e1(planted_anchor(thomas_res=1e-9))
        check("E1 fails Thomas at residual 1e-9 and keeps PCR",
              e["solver_ok"] == {"thomas": False, "pcr": True} and e["decision"].startswith("FAIL"))
        lv = planted_anchor()
        lv[1]["pcr"]["diff_scipy"] = 2e-8
        e = decide_e1(lv)
        check("E1 fails PCR at a 2e-8 difference against scipy", e["solver_ok"]["pcr"] is False)
        e = decide_e1(planted_anchor(ref_diff=1e-7))
        check("E1 flags references disagreeing at 1e-7", e["references_agree"] is False)
        e = decide_e1(planted_anchor(cusparse=False))
        check("E1 without cuSPARSE reads against scipy alone, 'one reference only'",
              e["decision"] == f"PASS; {LABEL_ONE_REF}" and e["references_agree"] is None)
        e = decide_e1(planted_anchor(pcr_res=float("nan")))
        check("E1 fails a non-finite residual", e["solver_ok"]["pcr"] is False)

    def planted_arith():
        for ctl in planted_controls():
            check(f"planted control {ctl['id']}: {ctl['metric']}", ctl["ok"], json.dumps(ctl["values"])[:600])

    def endpoints_planted():
        out = tmp / "pass"
        planted_env(out)
        init_state(out)
        apply_e1(out, decide_e1(planted_anchor()))
        write_planted_rows(out, planted_tables())
        rc = compute_endpoints(out)
        recs = read_records(out)
        dec = {k: recs[k]["decision"] for k in recs}
        check("endpoints on planted rows complete", rc == EXIT_OK, str(rc))
        check("E3 planted: if_lever, no noise label", dec.get("E3") == "if_lever", dec.get("E3"))
        e3 = recs["E3"]["values"]
        check("E3 planted speedups 2, 26.67, 256, 409.6, 409.6",
              all(same4(g, w) for g, w in zip(e3["speedups"], [2, 26.667, 256, 409.6, 409.6])), str(e3["speedups"]))
        check("E3 reports launch fraction at 2^10 and 2^24 (10 x 0.004 / 0.5 = 0.08)",
              same4(e3["launch_fraction_2e10"], 0.08) and e3["launch_fraction_2e24"] is not None)
        check("E4 planted: crossover 2^10 holds", dec.get("E4") == "HOLDS" and recs["E4"]["values"]["crossover_N"] == 1024,
              dec.get("E4"))
        check("E5 planted: 409.6 refuted above, ratio 14.63", dec.get("E5", "").startswith("REFUTED (above")
              and same4(recs["E5"]["values"]["measured_over_proxy"], 409.6 / 28), dec.get("E5"))
        check("E6 planted: g = 2, linear-like", dec.get("E6") == "linear-like" and same4(recs["E6"]["values"]["g"], 2))
        check("E7 planted: if_lever under the CPU baseline, speedup 4 at 2^24",
              dec.get("E7") == "if_lever under the CPU baseline" and same4(recs["E7"]["values"]["speedups"][-1], 4),
              dec.get("E7"))
        check("E8 planted: ratios 1.0, 1.1, 1.5, 2.9, 1.2 hold",
              dec.get("E8") == "HOLDS" and all(same4(g, w) for g, w in zip(recs["E8"]["values"]["ratios"],
                                                                         [1.0, 1.1, 1.5, 2.9, 1.2])), dec.get("E8"))
        check("E9 planted: PCR / cuSPARSE = 3 at every level",
              all(same4(v, 3) for v in recs["E9"]["values"]["pcr_over_cusparse"]))
        check("E10 planted: 2 h holds", dec.get("E10") == "HOLDS" and same4(recs["E10"]["values"]["hours"], 2),
              dec.get("E10"))
        check("report-only readings E6..E9 carry the role label",
              all(recs[k]["values"].get("role") == ROLE_REPORT_ONLY for k in ("E6", "E7", "E8", "E9")))
        check("every record carries run_valid, the dramaturg label and the baseline label",
              all(recs[k]["values"]["run_valid"] is True
                  and recs[k]["values"]["labels"]["card_dramaturg"] == LABEL_DRAMATURG
                  and recs[k]["values"]["labels"]["baseline"] == LABEL_BASELINE for k in recs))
        rec = json.loads(next((out / "records").glob("id-E3_*.json")).read_text())
        check("records are written by the frozen provenance writer (cell, inputs, decision_rule, env)",
              all(k in rec for k in ("cell", "inputs", "metric", "values", "threshold", "decision_rule", "decision",
                                     "env")) and rec["decision_rule"] == RULES["E3"]
              and all("sha256" in i for i in rec["inputs"]))
        pcr_rows = read_rows(out, "pcr_gpu")
        check("every PCR row carries launch_fraction after the launch probe",
              pcr_rows and all(is_num(r.get("launch_fraction")) for r in pcr_rows))
        out2 = tmp / "launch_bound"
        planted_env(out2)
        init_state(out2)
        apply_e1(out2, decide_e1(planted_anchor()))
        tabs = planted_tables()
        tabs["launch_probe"] = {N: {s: 0.04 for s in SEEDS} for N in LEVELS}
        write_planted_rows(out2, tabs)
        compute_endpoints(out2)
        check("E4 labels 'crossover at 2^10 is launch-bound' when the launch fraction is 0.8",
              read_records(out2)["E4"]["decision"] == "HOLDS (crossover at 2^10 is launch-bound)",
              read_records(out2)["E4"]["decision"])
        out3 = tmp / "incomplete"
        planted_env(out3)
        init_state(out3)
        apply_e1(out3, decide_e1(planted_anchor()))
        tabs = planted_tables()
        tabs["thomas_gpu"][2 ** 24][4] = float("nan")
        write_planted_rows(out3, tabs)
        compute_endpoints(out3)
        r3 = read_records(out3)
        check("a degenerate timing row voids the run and leaves E3 not run",
              r3["timing_rows_check"]["decision"].startswith("FAIL") and r3["E3"]["decision"].startswith("NOT_RUN")
              and r3["E3"]["values"]["run_valid"] is False)

    def zero_dispersion():
        out = tmp / "zero_dispersion"
        planted_env(out)
        init_state(out)
        apply_e1(out, decide_e1(planted_anchor()))
        write_planted_rows(out, planted_tables(zero_level=2 ** 18))
        rc = compute_endpoints(out)
        recs = read_records(out)
        check("zero dispersion of the noise-rule ratio halts WRONG_VARIANCE_SOURCE",
              rc == EXIT_WRONG_VARIANCE and recs["dispersion"]["decision"] == "WRONG_VARIANCE_SOURCE"
              and "E3" not in recs and load_state(out)["run_valid"] is False, f"rc={rc}")

    def propagation():
        ok, details = planted_gate_propagation(tmp / "propagation")
        for d in details:
            check("gate propagation: " + d["check"], d["ok"])
        check("gate propagation control passes as a whole", ok)

    def summary_and_words():
        out = tmp / "summary_empty"
        s = write_summary(out, EXIT_ENV, "cost guard inputs missing")
        check("summary with no stage run writes run_valid false and lists missing records",
              s["run_valid"] is False and "E3" in s["records_missing"] and (out / "m2_summary.json").exists())
        word = "repl" + "icat"
        texts = [(HERE / "run_m2.py").read_text().lower()]
        if (HERE / "onbox_m2.sh").exists():
            texts.append((HERE / "onbox_m2.sh").read_text().lower())
        check("no output text calls same-box reruns by the forbidden word", all(word not in t for t in texts))

    for fn in (parsers, source_and_command, numerics, rules_and_stats, detectors, e1_decisions, planted_arith,
               endpoints_planted, zero_dispersion, propagation, summary_and_words):
        group(fn)
    shutil.rmtree(tmp, ignore_errors=True)
    heavy = sorted(m for m in set(sys.modules) - before if m.split(".")[0] in ("numpy", "scipy"))
    check("selftest imported neither numpy nor scipy", not heavy, str(heavy[:5]))
    n_fail = sum(1 for _, ok in checks if not ok)
    print(f"selftest: {'PASS' if n_fail == 0 else 'FAIL'} ({len(checks) - n_fail} of {len(checks)} checks passed)",
          flush=True)
    return 0 if n_fail == 0 else 1


# ------------------------------------------------------------------------------------------------------------
# Command line
# ------------------------------------------------------------------------------------------------------------
STAGES = {
    "build": stage_build, "gpucheck": stage_gpucheck, "anchor": stage_anchor, "timers": stage_timers,
    "residual_sweep": stage_residual_sweep,
    "thomas_gpu": lambda ctx: run_gpu_arm(ctx, "thomas_gpu"), "pcr_gpu": lambda ctx: run_gpu_arm(ctx, "pcr_gpu"),
    "cusparse_gpu": lambda ctx: run_gpu_arm(ctx, "cusparse_gpu"),
    "thomas_batched_gpu": lambda ctx: run_gpu_arm(ctx, "thomas_batched_gpu"),
    "launch_probe": stage_launch_probe, "cpu_dgtsv": stage_cpu_dgtsv, "endpoints": stage_endpoints,
}
FAIL_CODE = {"build": EXIT_TOOLCHAIN, "gpucheck": EXIT_GPU}


def run_stage(name: str, ctx: Ctx) -> int:
    log(f"stage {name} start")
    try:
        rc = STAGES[name](ctx)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        rc = FAIL_CODE.get(name, EXIT_ERROR)
        if name in FAIL_CODE:
            void(ctx.out, f"stage {name}", f"unexpected error: {e!r}")
    log(f"stage {name} end rc={rc}")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", nargs="?", help="stage name, group name (extract, generate), summary, or guard")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=str(HERE / "results_m2" / "out"))
    ap.add_argument("--build", default=str(HERE / "results_m2" / "build"))
    ap.add_argument("--exit-code", type=int, default=0)
    ap.add_argument("--stop-reason", default="")
    ap.add_argument("--remote-timeout", default=None)
    ap.add_argument("--elapsed", default=None)
    ap.add_argument("--uptime", default=None)
    ap.add_argument("--price", default=None)
    ap.add_argument("--budget", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.stage:
        ap.print_help()
        return EXIT_ERROR
    ctx = Ctx(a.out, a.build)
    if a.stage == "summary":
        write_summary(ctx.out, a.exit_code, a.stop_reason)
        return EXIT_OK
    if a.stage == "guard":
        price, budget = parse_positive_float(a.price), parse_nonneg_float(a.budget)
        rt, el, up = parse_positive_float(a.remote_timeout), parse_nonneg_float(a.elapsed), parse_nonneg_float(a.uptime)
        if price is None or budget is None:
            print("BADENV PRICE_USD_PER_HOUR must be > 0 and BUDGET_LEFT_USD >= 0 (got "
                  f"{a.price!r}, {a.budget!r})")
            return EXIT_OK
        if rt is None or el is None or up is None:
            print(f"BADENV remote timeout, elapsed or uptime unreadable ({a.remote_timeout!r}, {a.elapsed!r}, {a.uptime!r})")
            return EXIT_OK
        verdict, detail = guard_decision(rt, el, up, price, budget)
        print(f"{verdict} {detail}")
        return EXIT_OK
    names = STAGE_GROUPS.get(a.stage, [a.stage])
    for name in names:
        if name not in STAGES:
            print(f"unknown stage {name!r}; stages: {', '.join(STAGE_ORDER)}", file=sys.stderr)
            return EXIT_ERROR
        rc = run_stage(name, ctx)
        if rc != EXIT_OK:
            return rc
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
