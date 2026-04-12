# Comparison Workflow

CAI is designed for comparative measurement, not only standalone runs.

A comparison workflow should answer:
- how does a stronger process shift the success curve?
- how does it change the hazard profile?
- does it alter the within/between variance structure?
- how does it change the gap profile `G(s)`?

## Minimal compare mode

A minimal comparison should run two process variants on the same ensemble and emit:
- paired success curves
- paired hazard curves
- paired variance summaries
- paired gap profiles when existence-side references are available

This release does not yet ship a full compare CLI, but the runtime and output contract are designed so that compare mode can be added without changing the scientific object.
