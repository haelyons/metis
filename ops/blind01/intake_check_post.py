"""After an authorized reader: validate its status files, scan for secrets, commit and push its folder. Prints only
validated enum statuses, an addendum prefix check, an independence-order check, counts, the agent's cost or tokens,
and push status; never file names or agent text.

Usage: python3 ~/.cache/blind01/intake_check_post.py [--dir intake_check|intake_check_codex|intake_acquire|intake_mirror|run5_diag|run6_diag|run6_diag2|run6_diag3|run7_diag|run7_diag2|run8_family|run8_diag|run8_diag2|run9_obs|run9_diag|run9_diag2|run9_diag3|run9_diag4|run9_replay|run9_par|run9_scale|run9_scale2|run9_replay2|run9_units|run9_outputs|run10_harness|run10_review|run10_harness2|run10_review2|run10_why|run10_mech|run10_inputs|run10_diff|run10_harness3|run10_review3] [--transcript NAME] [--check-only]
"""
import argparse, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default="intake_check", choices=["intake_check", "intake_check_codex", "intake_acquire", "intake_mirror", "run5_diag", "run6_diag", "run6_diag2", "run6_diag3", "run7_diag", "run7_diag2", "run8_family", "run8_diag", "run8_diag2", "run9_obs", "run9_diag", "run9_diag2", "run9_diag3", "run9_diag4", "run9_replay", "run9_par", "run9_scale", "run9_scale2", "run9_replay2", "run9_units", "run9_outputs", "run10_harness", "run10_review", "run10_harness2", "run10_review2", "run10_why", "run10_mech", "run10_inputs", "run10_diff", "run10_harness3", "run10_review3", "run10_post", "run10_post2", "run11_post", "run11_post2"])
ap.add_argument("--transcript", default="transcript.jsonl", choices=["transcript.jsonl", "codex.jsonl"])
ap.add_argument("--check-only", action="store_true")
a = ap.parse_args()

M = "/home/hal/dev/interp/metis"
D = "experiments/blind-01/m5/" + a.dir
P = os.path.join(M, D)
ENUMS = {
    "prerequisite": {"data", "licence_evidence", "data_and_licence_evidence", "other", "none_found"},
    "cause": {"transient_unreachable", "source_moved", "gated_access", "source_choice", "materials_missing", "other"},
    "materials_usable": {True, False},
    "run5_brief": {"addendum", "original"},
    "owner_action": {"none", "supply_materials", "obtain_access", "decide"},
}
if a.dir != "intake_check":
    ENUMS["alternative"] = {"none", "official_new_location", "archive_snapshot", "author_deposit", "verified_mirror",
                            "unverified_mirror"} | ({"regenerated_official"} if a.dir in ("intake_acquire", "intake_mirror") else set())
if a.dir == "run5_diag":
    ENUMS = {
        "failed_step": {"probe", "harness_agent", "harness_upload", "setup", "other", "unknown"},
        "upload_error": {"e2big", "other", "none", "unknown"},
        "upload_command_bytes": {"under_128k", "over_128k", "unknown"},
        "large_content": {"embedded_hashes", "embedded_data", "other", "not_large"},
        "hash_checks_requested": {True, False},
    }
if a.dir == "run6_diag":
    ENUMS = {
        "failure_point": {"script_error", "probe_paths", "missing_tool", "fetch_materials", "hash_mismatch", "build", "other", "unknown"},
        "same_cause_all_attempts": {True, False},
        "tail_had_cause": {"all", "some", "none", "unknown"},
        "repairs_targeted_cause": {"all", "some", "none", "unknown"},
        "mirror_from_box": {"reached_ok", "reached_failed", "not_reached", "unknown"},
        "fix_needs": {"harness_repair", "pipeline_repair_inputs", "materials", "brief", "box_image", "unknown"},
    }
if a.dir == "run6_diag2":
    ENUMS = {
        "tool_kind": {"downloader", "archive", "hash", "build", "cuda", "python_package", "other", "unknown"},
        "installable": {"apt_listed_source", "pip", "apt_unlisted_source", "not_installable", "unknown"},
        "rules_allow_fix": {"yes", "no", "unclear", "unknown"},
        "repair_lacked": {"probe_fact", "permission", "log_context", "nothing", "unknown"},
        "smallest_fix": {"probe_reports_tool", "rules_permit_install", "rules_clarify", "repair_prompt_context", "box_image", "unknown"},
    }
if a.dir == "run6_diag3":
    ENUMS = {
        "ubuntu_archive": {"main", "universe", "no", "unknown"},
        "pypi": {"yes", "no", "unknown"},
        "role": {"fetch_or_unpack", "build", "runtime_library", "other", "unknown"},
        "changes_stock_python": {"yes", "no", "unknown"},
    }
if a.dir == "run7_diag":
    point = {"script_error", "probe_paths", "missing_tool", "apt_install", "fetch_materials", "hash_mismatch", "build", "other", "unknown"}
    ENUMS = {
        "attempt1_point": point,
        "attempt2_point": point,
        "attempt3_point": point,
        "run6_library": {"installed_apt", "installed_other", "present_already", "not_needed", "failed", "unknown"},
        "furthest_phase": {"tool_install", "fetch_materials", "hash_check", "build", "smoke_or_anchor_prep", "other", "unknown"},
        "repair_regressed": {"yes", "no", "unknown"},
        "tail_had_cause": {"all", "some", "none", "unknown"},
        "repairs_targeted_cause": {"all", "some", "none", "unknown"},
        "mirror_from_box": {"reached_ok", "reached_failed", "not_reached", "unknown"},
        "hash_checks": {"all_passed", "some_failed", "not_reached", "unknown"},
        "fix_needs": {"harness_repair", "pipeline_repair_inputs", "pipeline_rules", "materials", "brief", "box_image", "unknown"},
    }
if a.dir == "run7_diag2":
    kind = {"syntax", "unbound_variable", "wrong_path", "command_usage", "control_flow", "environment", "other", "unknown"}
    ENUMS = {
        "error_kind_1": kind,
        "error_kind_2": kind,
        "error_kind_3": kind,
        "distinct_errors": {"all_distinct", "some_repeat", "same", "unknown"},
        "static_catch": {"all", "some", "none", "unknown"},
        "rule_induced": {"yes", "no", "unknown"},
        "rerun_refetches": {"yes", "partly", "no", "unknown"},
        "third_fix_outlook": {"likely_passes_setup", "likely_another_error", "unknown"},
        "smallest_fix": {"more_repairs", "static_check_before_upload", "harness_prompt_rule", "repair_prompt_context", "setup_split", "unknown"},
    }
if a.dir == "run8_family":
    family = {"codex", "opus", "opencode", "mixed", "none_run", "unknown"}
    ENUMS = {
        "codex_limit_error": {"yes", "no", "unknown"},
        "harness_family": {"codex", "opus", "opencode", "unknown"},
        "setup_repairs_family": family,
        "anchors_repairs_family": family,
        "call_lost": {"yes", "no", "unknown"},
        "course_changed": {"yes", "no", "unknown"},
    }
if a.dir == "run8_diag":
    point = {"script_error", "workload_error", "workload_too_long", "output_parse", "missing_input", "other", "unknown"}
    ENUMS = {
        "attempt1_point": point,
        "attempt2_point": point,
        "attempt3_point": point,
        "workload_completed": {"yes", "partly", "no", "unknown"},
        "budget_fit": {"fits", "too_small", "unknown"},
        "budget_source": {"intake_execution", "pipeline_default", "other", "unknown"},
        "measured_values": {"all", "some", "none", "unknown"},
        "out_size": {"under_100mb", "100mb_to_1gb", "over_1gb", "unknown"},
        "fetch_dominates_wall": {"yes", "no", "unknown"},
        "materials_issue": {"yes", "no", "unknown"},
        "tail_had_cause": {"all", "some", "none", "unknown"},
        "repairs_targeted_cause": {"all", "some", "none", "unknown"},
        "overrun_misled": {"yes", "no", "unknown"},
        "smallest_fix": {"more_anchor_repairs", "anchors_budget", "repair_prompt_context", "harness_prompt_rule", "output_size_rule", "materials", "brief", "unknown"},
    }
if a.dir == "run8_diag2":
    ENUMS = {
        "anchors_runtime": {"under_20m", "20m_to_1h", "1h_to_3h", "3h_to_6h", "6h_to_12h", "over_12h", "unknown"},
        "runtime_basis": {"published", "partial_progress", "both", "none"},
        "profile_same_workload": {"yes", "no", "unknown"},
        "profile_runtime_factor": {"under_2x", "2x_to_5x", "over_5x", "unknown"},
        "ceiling_fits_anchors": {"yes_with_repair", "yes_no_repair", "no", "unknown"},
        "scale": {"published", "reduced", "unknown"},
    }
if a.dir == "run9_obs":
    ENUMS = {
        "items_measured": {"all", "some", "none", "unknown"},
        "anchor_margin": {"comfortable", "near_edge", "inequality_met", "unknown"},
        "references_agree": {"close", "mixed", "far", "no_references", "unknown"},
        "measures_published_quantity": {"yes", "no", "unknown"},
        "scale": {"published", "reduced", "unknown"},
        "anchor_failures_cause": {"script_error", "output_format", "workload_error", "mixed", "unknown"},
        "reruns_repeated_workload": {"yes", "partly", "no", "unknown"},
        "out_size": {"under_1gb", "1gb_to_10gb", "10gb_to_100gb", "over_100gb", "unknown"},
        "fetch_dominates_wall": {"yes", "no", "unknown"},
        "profile_fits_time_left": {"yes", "no", "unknown"},
    }
if a.dir == "run9_diag":
    ENUMS = {
        "failure_source": {"run_command", "profiler", "resources", "workload", "fetch", "unknown"},
        "failure_point": {"early", "middle", "late", "unknown"},
        "fetch_share": {"under_25pct", "25_to_50pct", "over_50pct", "unknown"},
        "run_command_ran_before": {"yes", "no", "unknown"},
        "same_scale_as_anchors": {"yes", "no", "unknown"},
        "log_tail_has_cause": {"yes", "no", "unknown"},
        "repairable_by_harness_repair": {"yes", "no", "unknown"},
        "smallest_fix": {"profile_repair", "profiler_fix", "harness_prompt_rule", "fetch_scope", "resources", "unknown"},
    }
if a.dir == "run9_diag2":
    ENUMS = {
        "stats_files_present": {"all", "some", "none"},
        "reproduces_locally": {"yes", "no", "unknown"},
        "summariser_error": {"invalid_csv_row", "missing_csv_header", "missing_name_column", "unknown_time_unit", "missing_report_file",
                             "invalid_duration", "invalid_telemetry", "invalid_wall_or_origin", "json_decode", "other", "none", "unknown"},
        "failing_input": {"kern_sum", "mem_time_sum", "api_sum", "telemetry", "raw_wall", "other", "unknown"},
        "input_valid_nsys_format": {"yes", "no", "unknown"},
        "fix_location": {"profile_summarise", "profile_nsys", "both", "unknown"},
    }
if a.dir == "run9_diag3":
    ENUMS = {
        "kern_file_state": {"empty", "status_lines_only", "header_unmatched", "other"},
        "stats_log_says_no_kernel_data": {"yes", "no", "unknown"},
        "stats_log_says_skipped": {"yes", "no", "unknown"},
        "duration_column_form": {"not_applicable", "unit_not_in_parentheses", "different_column_word", "no_duration_column", "other"},
        "other_reports_parse": {"both", "one", "neither", "unknown"},
        "succeeds_if_kern_has_no_rows": {"yes", "no", "unknown"},
        "workload_has_cuda_kernels": {"yes", "no", "unknown"},
        "nsys_version": {"2023", "2024", "2025", "other", "unknown"},
    }
if a.dir == "run9_diag4":
    ENUMS = {
        "gpu_util_during_command": {"zero", "under_10pct", "10_to_50pct", "over_50pct", "unknown"},
        "compute_api": {"cuda", "opencl", "other_gpu", "cpu_only", "unknown"},
        "api_choice": {"published", "harness_or_intake_fallback", "unknown"},
        "nsys_capture_problem": {"yes", "no", "unknown"},
        "published_gpu_workload": {"yes", "no", "unknown"},
        "empty_reports_true_finding": {"yes", "no", "unknown"},
    }
if a.dir == "run9_replay":
    ENUMS = {
        "summariser_exit_u48": {"zero", "nonzero", "not_run"},
        "stage_count_ok": {"yes", "no", "unknown"},
        "wrapper_rule": {"none", "name", "within_2pct", "both", "unknown"},
        "timed_fraction_ok": {"yes", "no", "unknown"},
        "gpu_telemetry": {"true", "false", "unknown"},
        "gate_after_u48": {"pass", "numeric", "parse", "unknown"},
        "command_wall": {"under_10min", "10_to_60min", "1_to_2h", "2_to_4h", "over_4h", "unknown"},
        "probe_singles_fit_run9": {"yes", "no", "unknown"},
        "probe_fits_fresh_box": {"singles_and_batches", "singles_only", "no", "unknown"},
        "box_logical_cpus": {"under_8", "8_to_31", "32_to_63", "64_plus", "unknown"},
        "mps_for_cpu_only_command": {"verified", "mps_failed_then_plain", "unknown"},
    }
if a.dir == "run9_par":
    ENUMS = {
        "cpu_threads": {"single", "multi", "unknown"},
        "cpu_threads_basis": {"measured", "code_or_docs", "none"},
        "independent_units": {"yes", "partly", "no", "unknown"},
        "units_at_run_scale": {"one", "2_to_7", "8_to_63", "64_plus", "unknown"},
        "units_order": {"serial", "concurrent", "not_applicable", "unknown"},
        "per_unit_timing_saved": {"yes", "no"},
        "gpu_path_published": {"yes", "no", "unknown"},
        "more_units_changes_result": {"tighter_uncertainty", "closer_to_published_scale", "both", "neither", "unknown"},
        "published_uncertainty": {"yes", "no", "unknown"},
    }
if a.dir == "run9_scale":
    ENUMS = {
        "gated_anchors": {"one", "two_plus"},
        "references_within_tolerance": {"all", "some", "none", "no_references", "unknown"},
        "anchor_quantity": {"main", "secondary", "incidental", "unknown"},
        "scale_dimension": {"replicates_or_samples", "length_or_steps", "problem_size", "several", "not_reduced", "unknown"},
        "scale_factor": {"under_2x", "2_to_10x", "10_to_100x", "over_100x", "unknown"},
        "published_values_at_published_scale": {"yes", "no", "unknown"},
        "anchor_expectation": {"scale_invariant", "scale_dependent", "unknown"},
        "tolerance_vs_noise": {"much_wider", "comparable", "narrower", "deterministic", "unknown"},
        "tolerance_source": {"published_uncertainty", "intake_judgement", "other", "unknown"},
        "margin": {"under_25pct_used", "25_to_75pct_used", "over_75pct_used", "unknown"},
        "defect_detectable_run_scale": {"likely", "unlikely", "unknown"},
        "defect_detectable_published_scale": {"likely", "unlikely", "unknown"},
        "full_scale_adds": {"tighter_same_quantities", "more_quantities", "both", "nothing_beyond_noise", "unknown"},
        "full_scale_resolves_provenance": {"yes", "partly", "no", "unknown"},
        "published_scale_runtime": {"under_12h", "12_to_48h", "2_to_7d", "over_7d", "unknown"},
    }
if a.dir == "run9_scale2":
    ENUMS = {
        "comparison": {"equality_tolerance", "lower_threshold", "upper_threshold", "other", "unknown"},
        "published_value_scale": {"published_scale", "run_scale", "scale_free", "unknown"},
        "reduced_scale_effect": {"easier", "harder", "neither", "unknown"},
        "relative_difference": {"under_5pct", "5_to_20pct", "20_to_50pct", "over_50pct", "unknown"},
        "references_measure": {"same_quantity_other_conditions", "different_quantities", "mix", "unknown"},
        "best_description": {"calibration", "consistency_check", "weak_check", "unknown"},
    }
if a.dir == "run9_replay2":
    ENUMS = {
        "u48_failing_check": {"kernel_statement", "memory_statement", "api_statement", "telemetry", "wall", "other", "none"},
        "kernel_phrase": {"cuda_kernel_data", "other", "absent"},
        "memory_phrase": {"cuda_memory_data", "gpu_memory_data", "other", "absent"},
        "api_phrase": {"cuda_api_data", "cuda_trace_data", "other", "absent"},
        "patched_exit": {"zero", "nonzero", "not_run"},
        "stage_count_ok": {"yes", "no", "unknown"},
        "wrapper_rule": {"none", "name", "within_2pct", "both", "unknown"},
        "timed_fraction_ok": {"yes", "no", "unknown"},
        "gpu_telemetry": {"true", "false", "unknown"},
        "gate_after_fix": {"pass", "numeric", "parse", "unknown"},
    }
if a.dir == "run9_units":
    ENUMS = {
        "unit_kind": {"distinct_inputs", "repeated_trials", "candidates_same_input", "parameter_points", "chains_or_walkers", "mixed", "other", "unknown"},
        "reduced_dimension": {"inputs", "trials_per_input", "candidates_per_input", "parameter_points", "unit_length", "several", "unknown"},
        "expansion_effect": {"coverage", "precision", "per_input_outcome", "mixed", "none", "unknown"},
        "expansion_effect_basis": {"published_text", "code", "inferred", "none"},
        "combination": {"average_or_pooled", "best_or_max", "per_unit", "other", "unknown"},
        "unit_wall": {"under_1min", "1_to_10min", "10_to_60min", "over_60min", "unknown"},
        "unit_cost_cv": {"under_10pct", "10_to_50pct", "over_50pct", "unknown"},
        "subset_selectable": {"published_option", "config_edit", "code_change", "unknown"},
        "unit_output_repeatable": {"bitwise", "within_tolerance", "not_repeatable", "unknown"},
        "random_state": {"per_unit_independent", "sequence_dependent", "no_randomness", "unknown"},
        "thread_setting": {"all_cores_default", "fixed_number", "environment_variable", "unknown"},
        "threads_vs_cpus": {"under_half", "half_or_more", "unknown"},
        "writes_outside_out": {"no", "yes", "unknown"},
        "earlier_categories_merged": {"yes", "no"},
    }
if a.dir == "run9_outputs":
    ENUMS = {
        "per_unit_outputs": {"separate", "combined", "both", "unknown"},
        "unit_paths_stable": {"yes", "no", "not_applicable", "unknown"},
        "run_specific_content": {"no", "yes", "unknown"},
        "per_unit_costs_recorded": {"all_units", "some_units", "none", "unknown"},
        "subset_ids": {"args_safe", "args_unsafe_chars", "needs_file", "other", "unknown"},
        "units_count": {"under_4", "4_to_7", "8_to_15", "16_to_63", "64_or_more", "unknown"},
        "cuda_rows_zero": {"yes", "no", "unknown"},
        "telemetry_samples": {"none", "some", "unknown"},
        "telemetry_all_zero": {"yes", "no", "unknown"},
        "other_host_within_2pct": {"yes", "no", "unknown"},
        "cross_unit_state": {"no", "yes", "unknown"},
    }
if a.dir == "run10_harness":
    ENUMS = {
        "copies_written": {"yes", "no"},
        "units_listed": {"all_units", "some_units", "none"},
        "outputs_exist_in_reproduce": {"all", "some", "none"},
        "outputs_per_unit_only": {"yes", "no", "unknown"},
        "cost_source": {"reproduce_logs", "reproduce_outputs", "mixed", "unknown"},
        "subset_mechanism": {"published_option", "other", "unknown"},
        "command_differs_only_in_subset": {"yes", "no", "unknown"},
        "bash_syntax_ok": {"yes", "no"},
    }
if a.dir in ("run10_review", "run10_review2", "run10_review3"):
    ENUMS = {
        "diff_argument_handling": {"yes", "no"},
        "diff_subset_selection": {"yes", "no"},
        "diff_messages_or_log_paths": {"yes", "no"},
        "diff_output_locations": {"yes", "no"},
        "diff_environment": {"yes", "no"},
        "diff_thread_setting": {"yes", "no"},
        "diff_configuration_or_scale": {"yes", "no"},
        "diff_binary_or_entry": {"yes", "no"},
        "diff_working_directory": {"yes", "no"},
        "diff_other": {"yes", "no"},
        "same_computation_per_unit": {"yes", "no", "unknown"},
        "writes_only_out_or_temp": {"yes", "no", "unknown"},
        "mps_untouched": {"yes", "no"},
        "units_complete_and_ordered": {"yes", "no", "unknown"},
        "outputs_own_files_only": {"yes", "no", "unknown"},
        "costs_match_records": {"yes", "no", "unknown"},
        "contract_met": {"yes", "no", "unknown"},
        "verdict": {"usable", "needs_fix", "unknown"},
    }
if a.dir == "run10_harness2":
    ENUMS = {
        "copies_written": {"yes", "no"},
        "review_findings_resolved": {"all", "some", "none"},
        "units_json_changed": {"yes", "no"},
        "subset_mechanism": {"published_option", "other", "unknown"},
        "command_differs_only_in_subset": {"yes", "no", "unknown"},
        "same_computation_per_unit": {"yes", "no", "unknown"},
        "writes_only_out_or_temp": {"yes", "no", "unknown"},
        "bash_syntax_ok": {"yes", "no"},
    }
if a.dir == "run10_why":
    ENUMS = {
        "failed_requirement": {"subset_not_published_option", "computation_may_differ", "may_write_outside_out", "exit_status", "id_check", "output_paths", "units_json", "other", "none"},
        "entry_point_has_subset_option": {"yes", "no", "unknown"},
        "other_published_entry_same_computation": {"yes", "no", "not_needed", "unknown"},
        "fixable_in_unit_files": {"yes", "no", "unknown"},
        "probe_check_catches_wrong_computation": {"yes", "no", "partly", "unknown"},
        "risk_if_used_as_is": {"none", "wasted_run", "misleading_result", "unknown"},
        "unknowns_reason": {"static_reading_limit", "concrete_problem", "both", "unknown"},
    }
if a.dir == "run10_mech":
    ENUMS = {
        "mechanism": {"internal_same_code", "lower_level_published_tool", "modified_entry_copy", "reimplementation", "other", "unknown"},
        "per_unit_code_unmodified": {"yes", "no", "unknown"},
        "non_unit_share": {"none", "under_5pct", "5_to_25pct", "over_25pct", "unknown"},
        "skipped_steps_affect_unit_files": {"yes", "no", "no_steps_skipped", "unknown"},
        "partial_catch_reason": {"files_incomplete", "cost_can_change_silently", "both", "other", "unknown"},
        "cost_check_possible": {"yes", "no", "unknown"},
    }
if a.dir == "run10_inputs":
    ENUMS = {
        "restriction_possible": {"yes", "no", "unknown"},
        "restriction_kind": {"config_input_list", "scanned_directory", "command_line_inputs", "other", "none"},
        "published_code_unmodified": {"yes", "no", "not_applicable"},
        "same_paths": {"yes", "no", "not_applicable", "unknown"},
        "restriction_changes_computation": {"no", "yes", "not_applicable", "unknown"},
        "harness_rules_satisfiable": {"yes", "no", "not_applicable", "unknown"},
        "config_differs_only_in_units": {"yes", "no", "not_applicable", "unknown"},
    }
if a.dir == "run10_diff":
    ENUMS = {
        "baseline_vs_upstream": {"none", "config_or_environment", "source_patches", "both", "unknown"},
        "harness2_change_origin": {"inherited", "new_for_subsetting", "both", "unknown"},
        "inputs_change_origin": {"inherited", "new_for_subsetting", "both", "unknown"},
        "cli_selector": {"effective", "present_ineffective", "absent", "unknown"},
        "prepared_list_read": {"yes", "no", "unknown"},
        "list_redirectable": {"yes", "no_fixed_path", "not_applicable", "unknown"},
        "restricted_list_original_records": {"yes", "no", "not_applicable", "unknown"},
        "inherited_path_conflict": {"yes", "no", "unknown"},
        "route_adds_path_conflict": {"yes", "no", "not_applicable", "unknown"},
        "selection_affects_unit_results": {"no", "yes", "unknown"},
        "selection_effect_basis": {"code", "inferred", "none"},
        "full_run_repeatability_basis": {"two_runs_compared", "code_reading", "none"},
        "narrow_route_exists": {"yes", "no", "unknown"},
    }
if a.dir == "run10_harness3":
    ENUMS = {
        "copies_written": {"yes", "no"},
        "selection_route": {"restricted_prepared_list", "published_selector", "other"},
        "list_records_original": {"yes", "no", "unknown"},
        "list_passed_via_existing_input": {"yes", "no", "unknown"},
        "new_code_change": {"no", "yes"},
        "command_differs_only_in_selection": {"yes", "no", "unknown"},
        "adds_writes_outside_out": {"no", "yes", "unknown"},
        "inherited_path_conflict": {"yes", "no", "unknown"},
        "units_json_reused": {"yes", "no"},
        "bash_syntax_ok": {"yes", "no"},
    }
if a.dir == "run10_post":
    ENUMS = {
        "compared_files_nonempty": {"all", "some_empty", "unknown"},
        "subset_log_problems": {"none", "warnings_only", "errors", "unknown"},
        "cost_ratio_bucket": {"below_0_7", "0_7_to_1_3", "above_1_3", "null"},
        "outside_out_writes": {"none_found", "fixed_paths", "per_unit_paths", "per_invocation_paths", "mixed", "unknown"},
        "outside_out_location": {"temp_dir", "shared_run_directory", "home_or_cache", "multiple", "none", "unknown"},
        "concurrent_collision": {"none", "possible", "likely", "unknown"},
        "collision_detected_by_byte_check": {"yes", "partly", "no", "not_applicable", "unknown"},
        "avoidable_without_code_change": {"yes", "no", "not_needed", "unknown"},
        "avoidance_kind": {"existing_env_or_argument", "per_invocation_directory", "other", "none", "not_applicable"},
    }
    try:
        u = json.load(open(os.path.join(os.path.dirname(P), "run10", "agent", "results", "reproduce", "units_check.json")))
        r = u.get("cost_ratio")
        b = "null" if r is None else "below_0_7" if r < 0.7 else "0_7_to_1_3" if r <= 1.3 else "above_1_3"
        print("deterministic cost_ratio bucket:", b, "; files_total >= 4:", isinstance(u.get("files_total"), int) and u["files_total"] >= 4,
              "; files_matched == files_total:", u.get("files_matched") == u.get("files_total"))
    except Exception as e:
        print("deterministic check failed:", type(e).__name__)
if a.dir == "run10_post2":
    ENUMS = {
        "subset_errors_vs_run9": {"also_in_run9", "only_in_subset", "mixed", "no_errors", "unknown"},
        "subset_error_source": {"program_nonfatal", "environment_or_setup", "selection_or_restricted_list", "working_directory_or_links",
                                "path_conflict", "multiple", "other", "unknown"},
        "errors_affect_compared_outputs": {"no", "yes", "unknown"},
        "units_all_computed": {"yes", "no", "unknown"},
        "outputs_written_by_subset": {"yes", "no", "unknown"},
        "outside_out_naming": {"fixed", "per_unit", "per_invocation", "mixed", "none", "unknown"},
        "outside_out_purpose": {"scratch", "cache_reused_across_units", "intermediate_results", "logs", "multiple", "none", "unknown"},
        "later_units_read_earlier_writes": {"no", "yes", "unknown"},
        "private_copies_preserve_computation": {"yes", "no", "not_applicable", "unknown"},
    }
if a.dir == "run11_post":
    ENUMS = {
        "concurrent_log_problems": {"none", "same_as_serial", "new_in_concurrent", "unknown"},
        "outputs_cover_all_results": {"yes", "partly", "unknown"},
        "shared_writes_purpose": {"logs", "scratch", "cache_reused_across_invocations", "intermediate_results", "multiple", "none", "unknown"},
        "cross_invocation_reads": {"no", "yes", "unknown"},
        "less_work_in_later_invocations": {"no", "yes", "unknown"},
        "order_effect": {"none", "later_arms_faster", "later_arms_slower", "mixed", "unknown"},
        "factor_holds_against_nearest_serial": {"yes", "no", "unknown"},
        "gain_source": {"idle_cpu_in_serial_mode", "memory_or_io_overlap", "startup_or_serial_sections", "multiple", "other", "unknown"},
    }
    # Deterministic, content-free: concurrency.json holds no unit identifiers or paths (SCHEMAS.md, unit mode);
    # only fixed labels, booleans, ratios and counts are printed.
    try:
        c = json.load(open(os.path.join(os.path.dirname(P), "run11", "agent", "results", "reproduce", "out", "concurrency", "concurrency.json")))
        labels = ["a-1", "b-1", "c2-1", "c4-1", "c4-2", "c2-2", "b-2", "a-2"]
        arms = {arm["label"]: arm for arm in c["arms"] if arm.get("label") in labels}
        n = c["nproc"] if isinstance(c.get("nproc"), int) and c["nproc"] > 0 else None
        print("deterministic: mode units", c.get("mode") == "units", "; baseline_match", c.get("baseline_match") is True,
              "; outputs_match", c.get("outputs_match") is True, "; arms in order", [arm.get("label") for arm in c["arms"]] == labels)
        r = lambda x, y: round(x / y, 2) if isinstance(x, (int, float)) and isinstance(y, (int, float)) and y > 0 else None
        base = arms["a-1"]["wall_s"]
        for label in labels:
            arm = arms[label]
            print(" arm", label, "ok", arm["all_ok"] is True, "rc0", all(row.get("rc") == 0 for row in arm["invocations"]),
                  "wall/a-1", r(arm["wall_s"], base), "cores/nproc", r(arm["effective_cores"], n),
                  "busy", r(arm["busy_fraction"], 1), "threads/nproc", r(arm["threads_max"], n),
                  "shared_changes", arm["shared_changes"] if isinstance(arm["shared_changes"], int) else None)
        print(" replicate factors: a-1/c2-1", r(base, arms["c2-1"]["wall_s"]), "a-2/c2-2", r(arms["a-2"]["wall_s"], arms["c2-2"]["wall_s"]),
              "a-1/c4-1", r(base, arms["c4-1"]["wall_s"]), "a-2/c4-2", r(arms["a-2"]["wall_s"], arms["c4-2"]["wall_s"]),
              "; separate/serial", r(c["separate_wall_s"], c["serial_wall_s"]), "; nproc", n)
    except Exception as e:
        print("deterministic check failed:", type(e).__name__)
if a.dir == "run11_post2":
    ENUMS = {
        "concurrent_message_kind": {"resource_or_thread_limits", "shared_path_collision", "numerical_or_convergence", "timing_or_progress",
                                    "library_warning", "multiple", "other", "unknown"},
        "concurrent_messages_affect_results": {"no", "yes", "unknown"},
        "concurrent_messages_seen_before": {"yes", "partly", "no", "unknown"},
        "uncompared_files_kind": {"logs_or_timing", "run_metadata", "scientific_results", "multiple", "none", "unknown"},
        "uncompared_files_used_in_analysis": {"no", "yes", "unknown"},
        "uncompared_files_run_specific": {"yes", "no", "partly", "unknown"},
        "compared_files_hold_all_scientific_results": {"yes", "no", "unknown"},
        "coverage_extendable_without_code_change": {"yes", "no", "not_needed", "unknown"},
    }
if a.dir == "run10_review3":
    ENUMS = dict(ENUMS)
    ENUMS["restricted_list_faithful"] = {"yes", "no", "not_applicable", "unknown"}
    ENUMS["inherited_path_conflict"] = {"yes", "no", "unknown"}
    ENUMS["unit_files_add_path_conflict"] = {"no", "yes", "unknown"}
if a.dir == "intake_mirror":
    ENUMS["hashes_recorded"] = {True, False}
    ENUMS["refetch"] = {"match", "mismatch", "unreachable", "not_done"}


def git(*args):
    return subprocess.run(["git", "-C", M, *args], capture_output=True, text=True)


def load(name):
    try:
        s = json.load(open(os.path.join(P, name)))
        ok = isinstance(s, dict) and set(s) == set(ENUMS) and all(
            type(s[k]) is type(next(iter(v))) and s[k] in v for k, v in ENUMS.items())
    except Exception:
        s, ok = None, False
    return (s if ok else None)


status = load("status.json")
print("STATUS " + json.dumps(status, sort_keys=True) if status else "STATUS_INVALID")
if a.dir in ("run10_harness", "run10_harness2", "run10_harness3"):
    # Content-free checks of the written harness source against the U50 contract; prints booleans and buckets only.
    import hashlib, math
    source = os.path.join(os.path.dirname(P), "run9", "agent", "harness")
    digest = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
    names = sorted(os.listdir(source))
    print("copies identical:", all(os.path.isfile(os.path.join(P, n)) and digest(os.path.join(P, n)) == digest(os.path.join(source, n)) for n in names),
          "; source files", len(names))
    unit_id = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}")
    component = re.compile(r"[A-Za-z0-9._+=-]+")
    good_path = lambda q: isinstance(q, str) and all(component.fullmatch(c) and c not in (".", "..") for c in q.split("/"))
    try:
        u = json.load(open(os.path.join(P, "units.json")))["units"]
        valid = (isinstance(u, list) and len(u) >= 4 and len({r["id"] for r in u}) == len(u) and all(
            isinstance(r, dict) and set(r) == {"id", "outputs", "cost_s"} and isinstance(r["id"], str) and unit_id.fullmatch(r["id"])
            and isinstance(r["outputs"], list) and r["outputs"] and len(set(r["outputs"])) == len(r["outputs"])
            and all(good_path(q) for q in r["outputs"])
            and type(r["cost_s"]) in (int, float) and math.isfinite(r["cost_s"]) and r["cost_s"] > 0 for r in u))
        paths = [q for r in u for q in r["outputs"]] if valid else []
        out = os.path.join(os.path.dirname(P), "run9", "agent", "results", "reproduce", "out")
        found = sum(os.path.isfile(os.path.join(out, q)) for q in paths)
        n = len(u)
        print("units.json valid:", bool(valid), "; units", "under_4" if n < 4 else "4_to_7" if n < 8 else "8_to_15" if n < 16 else "16_to_63" if n < 64 else "64_or_more",
              "; output paths shared between units:", len(set(paths)) != len(paths),
              "; outputs in reproduce:", "none" if not paths or not found else "all" if found == len(paths) else "some")
    except Exception:
        print("units.json valid: False")
    script = os.path.join(P, "run_units.sh")
    print("run_units.sh present:", os.path.isfile(script), "; bash -n ok:",
          os.path.isfile(script) and subprocess.run(["bash", "-n", script], capture_output=True).returncode == 0)

if a.check_only:
    raise SystemExit(0)
if a.dir == "intake_check_codex":
    independent = load("status_independent.json")
    print("INDEPENDENT " + json.dumps(independent, sort_keys=True) if independent else "INDEPENDENT_INVALID")

addendum = os.path.join(P, "BRIEF_run5.md")
if a.dir in ("run5_diag", "run6_diag", "run6_diag2", "run6_diag3", "run7_diag", "run7_diag2", "run8_family", "run8_diag", "run8_diag2", "run9_obs", "run9_diag", "run9_diag2", "run9_diag3", "run9_diag4", "run9_replay", "run9_par", "run9_scale", "run9_scale2", "run9_replay2", "run9_units", "run9_outputs", "run10_harness", "run10_review", "run10_harness2", "run10_review2", "run10_why", "run10_mech", "run10_inputs", "run10_diff", "run10_harness3", "run10_review3", "run10_post", "run10_post2", "run11_post", "run11_post2"):
    pass
elif os.path.exists(addendum):
    original = open(os.path.join(M, "experiments/blind-01/m5/BRIEF.md"), "rb").read()
    text = open(addendum, "rb").read()
    print("addendum present; starts with original brief:", text.startswith(original) and len(text) > len(original),
          "; status agrees:", bool(status) and status["run5_brief"] == "addendum")
    if a.dir == "intake_mirror":
        extra = text[len(original):]
        print("addendum section heading:", b"## Materials (owner decision 2026-10-31; recorded by an authorized reader agent)" in extra,
              "; names unverified_mirror:", b"unverified_mirror" in extra,
              "; sha256 values:", len(set(re.findall(rb"\b[0-9a-f]{64}\b", extra))))
else:
    print("addendum absent; status agrees:", bool(status) and status["run5_brief"] == "original")

try:
    rows = [json.loads(line) for line in open(os.path.join(P, a.transcript)) if line.strip()]
    if a.transcript == "codex.jsonl":
        usage = [r.get("usage") or {} for r in rows if r.get("type") == "turn.completed"]
        print("agent turns", len(usage), "tokens_in", sum(u.get("input_tokens", 0) for u in usage),
              "tokens_out", sum(u.get("output_tokens", 0) for u in usage))
        # Phase A must write status_independent.json before any command or edit touches the Opus reader's folder.
        # Only the command text and edited paths count, not command output (a listing may name the folder).
        items = [r.get("item") or {} for r in rows if r.get("type") == "item.completed"]
        acts = [it.get("command", "") if it.get("type") == "command_execution" else json.dumps(it.get("changes"))
                for it in items if it.get("type") in ("command_execution", "file_change")]
        opus = next((i for i, t in enumerate(acts) if re.search(r"intake_check/", t)), None)
        wrote = next((i for i, t in enumerate(acts) if "status_independent.json" in t), None)
        if a.dir == "intake_check_codex":
            print("independent status written before touching the Opus reader's folder:",
                  "unknown" if wrote is None else (opus is None or wrote < opus))
    else:
        last = rows[-1]
        print("agent turns", last.get("num_turns"), "usd", round(last.get("total_cost_usd") or 0, 2),
              "error", last.get("is_error"))
except Exception:
    print("agent result unreadable")

keys = []
for line in open("/home/hal/dev/interp/dm_hack/.keys"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= 12:
            keys.append(value.encode())
TOKEN = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                   rb"|secret_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")
keep, held = [], 0
for root, _, names in os.walk(P):
    for name in names:
        f = os.path.join(root, name)
        data = open(f, "rb").read()
        if os.path.getsize(f) > 95 * 1024 * 1024 or any(k in data for k in keys) or TOKEN.search(data):
            held += 1
        else:
            keep.append(os.path.relpath(f, M))
print("files to commit", len(keep), "held back (secret pattern or >95 MB)", held)
if keep:
    git("add", "-f", "--", *keep)
    c = git("commit", "-q", "-m", f"blind-01 m5: authorized {a.dir.replace('_', ' ')} (reader agent; operator sees enum status only)\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
            "Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3")
    git("push", "-q", "origin", "main")
    git("fetch", "-q", "origin")
    head, remote = git("rev-parse", "HEAD").stdout.strip(), git("rev-parse", "origin/main").stdout.strip()
    print("PUSH_OK " + head[:8] if c.returncode == 0 and head == remote else "COMMIT_OR_PUSH_FAILED")
