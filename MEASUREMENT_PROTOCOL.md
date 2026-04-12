# Measurement Protocol

The Constructive Accessibility Instrument records a constructive process as a stream of receipts and derives a standard diagnostic suite from those receipts.

## Core observables

### Success curve
Success rate as a function of the control parameter. This shows where constructive accessibility begins to fail.

### Hazard profile
Step-indexed failure hazard. This reveals *when* the process dies along the trajectory rather than only whether it succeeds.

### Variance decomposition
A weighted Bernoulli decomposition into:
- within-instance variance
- between-instance variance

This distinguishes “hard instances” from “path-dependent failure on typical instances.”

### Gap profile `G(s)`
Given an existence curve `E(alpha)` and a reachability curve `R(alpha)`, the gap profile is

`G(s) = alpha_E(s) - alpha_R(s)`

where `alpha_E(s)` and `alpha_R(s)` are the control-parameter locations at which the two curves fall to the same viability level `s`.

## Why receipts matter

Traditional benchmarking keeps the output and discards the internal process bookkeeping. CAI upgrades that bookkeeping to primary observables. The receipt stream is the experimental record.

## Why compare processes

The instrument is designed not only for single-process runs, but for side-by-side comparison of process variants on the same benchmark ensemble using the same observables.
