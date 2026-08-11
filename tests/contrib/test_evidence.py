import json

import pytest

from minisweagent.contrib.evidence import GateError, TCFlowRunResult, load_run_result


def passing_result(**overrides: object) -> TCFlowRunResult:
    values = {
        "version": "tc-flow-run-result-v1",
        "run_id": "run-1",
        "feature": "fix-config-validation",
        "contract_hash": "a" * 64,
        "target_repository": "acme/tool",
        "target_issue": 42,
        "task_review": "pass",
        "feature_qa": "pass",
        "stop_hook": "ALLOW",
        "repository_policy": "local-pass",
        "tests": [{"command": "pytest", "status": "pass", "summary": "12 passed"}],
        "blockers": [],
    }
    values.update(overrides)
    return TCFlowRunResult.model_validate(values)


def test_evidence_requires_exact_target_and_no_blockers() -> None:
    passing_result().assert_publishable("acme/tool", 42)

    with pytest.raises(GateError, match="target repository"):
        passing_result().assert_publishable("other/tool", 42)
    with pytest.raises(GateError, match="blocker"):
        passing_result(blockers=["maintainer asked to wait"]).assert_publishable("acme/tool", 42)


def test_evidence_requires_successful_test() -> None:
    with pytest.raises(GateError, match="successful test"):
        passing_result(tests=[]).assert_publishable("acme/tool", 42)


def test_load_run_result_rejects_failed_gate(tmp_path) -> None:
    payload = passing_result().model_dump(mode="json")
    payload["feature_qa"] = "repair"
    path = tmp_path / "run-result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(GateError, match="Feature QA"):
        load_run_result(path)


def test_load_run_result_rejects_malformed_contract_hash(tmp_path) -> None:
    payload = passing_result().model_dump(mode="json")
    payload["contract_hash"] = "not-a-commitment"
    path = tmp_path / "run-result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(GateError, match="Invalid TC Flow"):
        load_run_result(path)
