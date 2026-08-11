import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class GateError(RuntimeError):
    pass


class TestEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    command: str
    status: str
    summary: str


class TCFlowRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["tc-flow-run-result-v1"]
    run_id: str
    feature: str
    contract_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_repository: str
    target_issue: int
    task_review: str
    feature_qa: str
    stop_hook: str
    repository_policy: str
    tests: list[TestEvidence]
    blockers: list[str]

    def assert_gates(self) -> None:
        checks = (
            (self.task_review == "pass", "Task Review did not pass"),
            (self.feature_qa == "pass", "Feature QA did not pass"),
            (self.stop_hook == "ALLOW", "Stop Hook did not allow publication"),
            (
                self.repository_policy in {"local-pass", "remote-pass"},
                "Repository Policy did not pass",
            ),
            (any(test.status == "pass" for test in self.tests), "No successful test evidence was supplied"),
            (not self.blockers, "TC Flow result contains a blocker"),
        )
        for passed, message in checks:
            if not passed:
                raise GateError(message)

    def assert_publishable(self, repository: str, issue_number: int) -> None:
        self.assert_gates()
        if self.target_repository != repository:
            raise GateError(f"TC Flow target repository is {self.target_repository}, not {repository}")
        if self.target_issue != issue_number:
            raise GateError(f"TC Flow target issue is #{self.target_issue}, not #{issue_number}")


def load_run_result(path: Path) -> TCFlowRunResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = TCFlowRunResult.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise GateError(f"Invalid TC Flow run result: {error.__class__.__name__}") from error
    result.assert_gates()
    return result
