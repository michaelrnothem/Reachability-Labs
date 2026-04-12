from reachability_labs_demo.runtime import TrialResult, summarize_results


def test_variance_decomposition_sums_to_total():
    rows = [
        TrialResult(alpha=1.0, n=10, instance_index=0, branch_index=0, trial_index=0, instance_seed=0, process_seed=0, success=True, death_step=None, final_step=10, receipts=[]),
        TrialResult(alpha=1.0, n=10, instance_index=0, branch_index=1, trial_index=1, instance_seed=0, process_seed=1, success=False, death_step=9, final_step=9, receipts=[]),
        TrialResult(alpha=1.0, n=10, instance_index=1, branch_index=0, trial_index=2, instance_seed=1, process_seed=2, success=False, death_step=8, final_step=8, receipts=[]),
        TrialResult(alpha=1.0, n=10, instance_index=1, branch_index=1, trial_index=3, instance_seed=1, process_seed=3, success=False, death_step=8, final_step=8, receipts=[]),
    ]
    _, _, variance_rows = summarize_results(rows)
    row = variance_rows[0]
    total = float(row['total_var'])
    within = float(row['within_var'])
    between = float(row['between_var'])
    assert abs((within + between) - total) < 1e-12
