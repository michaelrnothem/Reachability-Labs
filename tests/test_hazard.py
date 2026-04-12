from reachability_labs_demo.runtime import TrialResult, summarize_results


def test_hazard_mass_zero_when_all_success():
    rows = [TrialResult(alpha=1.0, n=10, instance_index=i, branch_index=0, trial_index=i, instance_seed=i, process_seed=i, success=True, death_step=None, final_step=10, receipts=[]) for i in range(4)]
    _, hazard_rows, _ = summarize_results(rows)
    assert all(float(r['hazard']) == 0.0 for r in hazard_rows)


def test_hazard_contains_terminal_death_mass_when_all_fail_same_step():
    rows = [TrialResult(alpha=1.0, n=10, instance_index=i, branch_index=0, trial_index=i, instance_seed=i, process_seed=i, success=False, death_step=3, final_step=3, receipts=[]) for i in range(4)]
    _, hazard_rows, _ = summarize_results(rows)
    target = [r for r in hazard_rows if int(r['step']) == 3]
    assert target and abs(float(target[0]['hazard']) - 1.0) < 1e-9
