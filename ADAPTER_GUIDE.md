# Adapter Guide

An adapter turns a constructive process into something the Constructive Accessibility Instrument can measure.

## Required methods

Every adapter must supply the following runtime-facing methods:

- `make_instance(n, alpha, seed)` — generate one benchmark instance
- `init_state(instance)` — place the process at its origin
- `step_index(state)` — return the current construction step
- `all_local_moves(instance, state)` — enumerate all currently available local moves
- `sample_moves(instance, state, rng, budget)` — optional sampled proposer approximation
- `judge_move(instance, state, move)` — legality + score + telemetry for a candidate move
- `apply_move(instance, state, move)` — commit the move and return the next state
- `is_complete(instance, state)` — whether construction has finished
- `is_success(instance, state)` — whether the completed state passes the success gate
- `receipt_extras(instance, state)` — extra per-step observables recorded into receipts

## What a receipt is

A receipt is a per-step record of what the process revealed about the world at that step:

- pool size
- valid move count
- chosen move and score
- adapter-specific extras such as unit pressure or frontier width

CAI treats these receipts as **primary observables**, not just implementation scaffolding.

## Minimum viable adapter

A minimal adapter only needs:

1. a generator for benchmark instances
2. a state object
3. local move enumeration
4. a legality/score rule
5. a success criterion

The flagship 3-SAT adapter is the simplest complete example in this release.

## Stronger adapters

A stronger adapter may additionally provide:

- exact-local vs sampled proposer variants
- richer receipt fields
- existence-side reference data for gap profiling
- multiple process variants for comparison workflows

## What outputs the runtime expects

The runtime standardizes outputs into:

- `summary_by_alpha.csv`
- `hazard_by_alpha.csv`
- `variance_by_alpha.csv`
- `receipts/*.csv`
- `run_manifest.json`

A reusable adapter should fit this output contract.
