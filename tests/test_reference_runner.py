import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.hwr_adapter_runtime import run_adapter_stage
from tools.hwr_openai_adapter import (
    AdapterError as OpenAIAdapterError,
    parse_structured_response,
    response_request,
)
from tools.hwr_workflow import resume_editorial_workflow, run_editorial_workflow
from tools.hwr_reference import (
    HwrError,
    apply_artifact_record,
    apply_content_design,
    apply_review_record,
    apply_visual_record,
    build_adapter_packet,
    build_intake_plan,
    build_run_plan,
    create_source_snapshot,
    doctor,
    finalize_run,
    load_task_with_source_snapshots,
    load_repository,
    resolve_modules,
    validate_source_snapshot,
    validate_run_record,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "starter-kit/.human-writing-rules/config.json"
READY_TASK_PATH = ROOT / "examples/tasks/ru-science-article.json"
BLOCKED_TASK_PATH = ROOT / "examples/tasks/ru-blocked-unsupported-claim.json"
DESIGN_PATH = ROOT / "examples/transitions/ru-science-design.json"
DRAFT_PATH = ROOT / "examples/transitions/ru-science-draft.json"
EDIT_PATH = ROOT / "examples/transitions/ru-science-edit.json"
REVIEW_PATH = ROOT / "examples/transitions/ru-science-review.json"
CLI_PATH = ROOT / "tools/hwr.py"
FIXTURE_ADAPTER_PATH = ROOT / "tools/hwr_fixture_adapter.py"
OPENAI_ADAPTER_PATH = ROOT / "tools/hwr_openai_adapter.py"
OPENAI_DESIGN_FIXTURE_PATH = (
    ROOT / "examples/provider-fixtures/openai-design-response.json"
)
OPENAI_VISUAL_FIXTURE_PATH = (
    ROOT / "examples/provider-fixtures/openai-visual-response.json"
)
MYSTICISM_PILOT_PATH = ROOT / "examples/pilot-runs/ru-mysticism"


class ReferenceRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = load_repository(ROOT)
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.ready_task = json.loads(READY_TASK_PATH.read_text(encoding="utf-8"))
        cls.blocked_task = json.loads(BLOCKED_TASK_PATH.read_text(encoding="utf-8"))
        cls.design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
        cls.draft = json.loads(DRAFT_PATH.read_text(encoding="utf-8"))
        cls.edit = json.loads(EDIT_PATH.read_text(encoding="utf-8"))
        cls.review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))

    def test_doctor_reports_offline_capabilities_and_digest(self) -> None:
        result = doctor(self.repository)

        self.assertTrue(result["ready"])
        self.assertEqual("offline", result["mode"])
        self.assertFalse(result["auth_required"])
        self.assertEqual(60, result["object_count"])
        self.assertRegex(result["registry_revision"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual("not-configured", result["model_adapter"])
        self.assertEqual(
            "available-not-configured",
            result["provider_adapters"][0]["status"],
        )

    def test_resolution_is_minimal_ordered_and_revision_pinned(self) -> None:
        resolution = resolve_modules(
            self.repository,
            self.config,
            self.ready_task,
        )

        self.assertEqual(self.config["registry_revision"], resolution["registry_revision"])
        self.assertIn("format.article.foundation", resolution["root_objects"])
        self.assertIn("topic.science.foundation", resolution["root_objects"])
        self.assertIn("rule.visual-integrity", resolution["root_objects"])
        self.assertEqual(
            len(resolution["dependency_order"]),
            len(set(resolution["dependency_order"])),
        )

        positions = {
            object_id: index
            for index, object_id in enumerate(resolution["dependency_order"])
        }
        for object_id in resolution["dependency_order"]:
            for dependency in self.repository["by_id"][object_id].get("requires", []):
                self.assertLess(positions[dependency], positions[object_id])

    def test_unknown_topic_uses_declared_general_fallback(self) -> None:
        config = copy.deepcopy(self.config)
        config["topic"] = "unlisted-topic"

        resolution = resolve_modules(self.repository, config)

        self.assertEqual("general", resolution["inputs"]["topic"])
        self.assertEqual("fallback", resolution["origins"]["topic"])
        self.assertEqual("unlisted-topic", resolution["fallbacks"][0]["input"])

    def test_unknown_skill_is_rejected_without_fuzzy_matching(self) -> None:
        config = copy.deepcopy(self.config)
        config["skill"] = "scientific-news"

        with self.assertRaises(HwrError) as raised:
            resolve_modules(self.repository, config)

        self.assertEqual("UNKNOWN_SKILL", raised.exception.code)

    def test_ready_task_builds_context_ready_plan(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)

        self.assertEqual("context-ready", run["state"])
        self.assertIsNone(run["blocked_stage"])
        self.assertEqual([], run["blockers"])
        self.assertEqual("pass", run["gates"]["context"]["status"])
        self.assertEqual("ready", run["gates"]["media"]["status"])
        self.assertEqual("planned", run["output_package"]["visual_assets"]["status"])
        self.assertEqual([], validate_run_record(self.repository, run))

    def test_agent_led_intake_asks_a_bounded_first_round(self) -> None:
        intake = build_intake_plan(
            self.repository,
            self.config,
            {"task_id": "interactive-intake"},
            limit=3,
        )

        self.assertEqual("questions-required", intake["status"])
        self.assertEqual(5, intake["questions_total"])
        self.assertEqual(2, intake["remaining_question_count"])
        self.assertEqual(
            [
                "Q-SUBJECT",
                "Q-AUDIENCE-INTENT",
                "Q-CENTRAL-QUESTION",
            ],
            [question["id"] for question in intake["question_batch"]],
        )
        self.assertNotIn(
            '{"description"',
            intake["question_batch"][1]["prompt"],
        )
        self.assertIn(
            "Любознательные читатели",
            intake["question_batch"][1]["prompt"],
        )
        self.assertIn(
            "EMPTY_CLAIM_LEDGER",
            {action["code"] for action in intake["agent_actions"]},
        )
        self.assertNotIn(
            "EMPTY_CLAIM_LEDGER",
            {question["id"] for question in intake["question_batch"]},
        )

    def test_agent_led_intake_is_ready_after_explicit_answers(self) -> None:
        task = copy.deepcopy(self.ready_task)
        for field in (
            "language",
            "locale",
            "content_type",
            "topic",
            "platform",
            "skill",
            "tone",
            "audience",
            "intent",
            "author_perspective",
            "risk_level",
        ):
            task[field] = copy.deepcopy(self.config[field])
        task["visuals"] = copy.deepcopy(self.config["visuals"])

        intake = build_intake_plan(
            self.repository,
            self.config,
            task,
        )

        self.assertEqual("ready", intake["status"])
        self.assertEqual([], intake["question_batch"])
        self.assertEqual([], intake["agent_actions"])
        self.assertEqual({}, intake["proposed_defaults"])

    def test_agent_led_intake_rejects_unbounded_question_batch(self) -> None:
        with self.assertRaises(HwrError) as raised:
            build_intake_plan(
                self.repository,
                self.config,
                {"task_id": "interactive-intake"},
                limit=6,
            )

        self.assertEqual("INVALID_LIMIT", raised.exception.code)

    def test_cli_emits_agent_led_intake_without_task_file(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--json",
                "runs",
                "questions",
                "--config",
                str(CONFIG_PATH),
                "--limit",
                "2",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual("runs.questions", envelope["command"])
        self.assertEqual(
            ["Q-SUBJECT", "Q-AUDIENCE-INTENT"],
            [
                question["id"]
                for question in envelope["data"]["question_batch"]
            ],
        )
        self.assertEqual(3, envelope["data"]["remaining_question_count"])

    def test_cli_rejects_more_than_five_intake_questions(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--json",
                "runs",
                "questions",
                "--config",
                str(CONFIG_PATH),
                "--limit",
                "6",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(2, result.returncode)
        envelope = json.loads(result.stdout)
        self.assertFalse(envelope["ok"])
        self.assertEqual("INVALID_LIMIT", envelope["error"]["code"])

    def test_source_snapshot_is_hashed_and_reaches_adapter_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            material_path = source_root / "materials/evidence.md"
            material_path.parent.mkdir()
            material = "# Evidence\n\nA bounded local source.\n"
            material_path.write_text(material, encoding="utf-8")
            snapshot = create_source_snapshot(
                "materials/evidence.md",
                source_root=source_root,
                source_id="SRC-001",
                snapshot_id="SNAP-001",
                media_type="text/markdown",
                captured_at="2026-07-26",
            )
            snapshot_path = source_root / "snapshots/SRC-001.json"
            snapshot_path.parent.mkdir()
            snapshot_path.write_text(
                json.dumps(snapshot, ensure_ascii=False),
                encoding="utf-8",
            )

            task = copy.deepcopy(self.ready_task)
            task["sources"][0]["snapshot_path"] = "snapshots/SRC-001.json"
            task_path = source_root / "task.json"
            task_path.write_text(
                json.dumps(task, ensure_ascii=False),
                encoding="utf-8",
            )

            hydrated = load_task_with_source_snapshots(task_path)
            run = build_run_plan(self.repository, self.config, hydrated)
            packet = build_adapter_packet(self.repository, run, "design")

        expected_digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        self.assertEqual(
            f"sha256:{expected_digest}",
            snapshot["sha256"],
        )
        self.assertEqual(material, packet["sources"][0]["snapshot"]["content"])
        self.assertNotIn(
            "content",
            run["output_package"]["source_notes"]["sources"][0]["snapshot"],
        )
        self.assertEqual([], validate_source_snapshot(snapshot))
        self.assertEqual([], validate_run_record(self.repository, run))

    def test_source_snapshot_rejects_escape_and_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            material_path = source_root / "material.txt"
            material_path.write_text("trusted", encoding="utf-8")

            with self.assertRaises(HwrError) as escaped:
                create_source_snapshot(
                    "../outside.txt",
                    source_root=source_root,
                    source_id="SRC-001",
                    snapshot_id="SNAP-001",
                    media_type="text/plain",
                )
            self.assertEqual("UNSAFE_SOURCE_PATH", escaped.exception.code)

            snapshot = create_source_snapshot(
                "material.txt",
                source_root=source_root,
                source_id="SRC-001",
                snapshot_id="SNAP-001",
                media_type="text/plain",
            )
            snapshot["content"] = "tampered"
            snapshot_path = source_root / "snapshot.json"
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            task = copy.deepcopy(self.ready_task)
            task["sources"][0]["snapshot_path"] = "snapshot.json"
            task_path = source_root / "task.json"
            task_path.write_text(json.dumps(task), encoding="utf-8")

            with self.assertRaises(HwrError) as tampered:
                load_task_with_source_snapshots(task_path)
            self.assertEqual("SOURCE_SNAPSHOT_INVALID", tampered.exception.code)
            self.assertIn("sha256 does not match", repr(tampered.exception.details))

    def test_source_snapshot_rejects_oversized_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_root = Path(temporary_directory)
            material_path = source_root / "oversized.txt"
            material_path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))

            with self.assertRaises(HwrError) as oversized:
                create_source_snapshot(
                    "oversized.txt",
                    source_root=source_root,
                    source_id="SRC-001",
                    snapshot_id="SNAP-001",
                    media_type="text/plain",
                )
            self.assertEqual("SOURCE_TOO_LARGE", oversized.exception.code)

    def test_source_snapshot_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            source_root = temporary / "allowed"
            source_root.mkdir()
            outside = temporary / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            link = source_root / "linked.txt"
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("symlinks are unavailable in this environment")

            with self.assertRaises(HwrError) as escaped:
                create_source_snapshot(
                    "linked.txt",
                    source_root=source_root,
                    source_id="SRC-001",
                    snapshot_id="SNAP-001",
                    media_type="text/plain",
                )
            self.assertEqual("UNSAFE_SOURCE_PATH", escaped.exception.code)

    def test_cli_creates_and_loads_source_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            (temporary / "material.md").write_text(
                "Local source for the adapter.\n",
                encoding="utf-8",
            )
            snapshot_path = temporary / "snapshots/SRC-001.json"
            created = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "sources",
                    "snapshot",
                    "--input",
                    "material.md",
                    "--source-root",
                    str(temporary),
                    "--source-id",
                    "SRC-001",
                    "--snapshot-id",
                    "SNAP-CLI-001",
                    "--media-type",
                    "text/markdown",
                    "--out",
                    str(snapshot_path),
                ],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, created.returncode, created.stderr)
            self.assertEqual(
                "sources.snapshot",
                json.loads(created.stdout)["command"],
            )

            task = copy.deepcopy(self.ready_task)
            task["sources"][0]["snapshot_path"] = "snapshots/SRC-001.json"
            task_path = temporary / "task.json"
            task_path.write_text(
                json.dumps(task, ensure_ascii=False),
                encoding="utf-8",
            )
            planned = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "runs",
                    "plan",
                    "--config",
                    str(CONFIG_PATH),
                    "--task",
                    str(task_path),
                ],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, planned.returncode, planned.stderr)
            run = json.loads(planned.stdout)["data"]
            self.assertEqual(
                "Local source for the adapter.\n",
                run["sources"][0]["snapshot"]["content"],
            )

    def test_unsupported_claim_produces_explicit_blockers(self) -> None:
        run = build_run_plan(self.repository, self.config, self.blocked_task)

        self.assertEqual("blocked", run["state"])
        self.assertEqual("context-gate", run["blocked_stage"])
        codes = {entry["code"] for entry in run["blockers"]}
        self.assertTrue(
            {
                "MISSING_REQUIRED_SOURCES",
                "SOURCE_FRESHNESS_UNRESOLVED",
                "UNSUPPORTED_MATERIAL_CLAIM",
            }.issubset(codes)
        )
        self.assertEqual([], validate_run_record(self.repository, run))

    def test_first_person_requires_authorized_material(self) -> None:
        task = copy.deepcopy(self.ready_task)
        task["author_perspective"] = "first-person"
        task["assessments"]["perspective"] = "unknown"

        run = build_run_plan(self.repository, self.config, task)

        self.assertEqual("blocked", run["state"])
        self.assertIn(
            "UNAUTHORIZED_PERSPECTIVE",
            {entry["code"] for entry in run["blockers"]},
        )

    def test_required_visual_cannot_resolve_to_none(self) -> None:
        task = copy.deepcopy(self.ready_task)
        task["visuals"] = {"mode": "required"}
        task["media"] = {
            "decision": "none",
            "reason": "Fixture intentionally conflicts with required mode.",
        }

        run = build_run_plan(self.repository, self.config, task)

        self.assertEqual("blocked", run["state"])
        self.assertEqual("visual-gate", run["blocked_stage"])
        self.assertIn(
            "REQUIRED_VISUAL_OMITTED",
            {entry["code"] for entry in run["blockers"]},
        )

    def test_run_validation_detects_stale_dependency_order(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        order = run["resolution"]["dependency_order"]
        article_index = order.index("format.article.foundation")
        pipeline_index = order.index("core.writing-pipeline")
        order[article_index], order[pipeline_index] = (
            order[pipeline_index],
            order[article_index],
        )

        errors = validate_run_record(self.repository, run)

        self.assertTrue(
            any("dependency order places" in error for error in errors),
            errors,
        )

    def test_run_validation_requires_schema_complete_blocked_state(self) -> None:
        run = build_run_plan(self.repository, self.config, self.blocked_task)
        run.pop("content_design")
        run["blocked_stage"] = None

        errors = validate_run_record(self.repository, run)

        self.assertTrue(
            any("content_design" in error for error in errors),
            errors,
        )
        self.assertIn("blocked state requires blocked_stage", errors)

    def test_run_validation_does_not_crash_on_wrong_nested_types(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        run["resolution"]["dependency_order"] = None
        run["gates"]["context"] = "pass"
        run["review_plan"][0]["reviewer_id"] = {}
        run["output_package"]["publication_copy"] = []

        errors = validate_run_record(self.repository, run)

        self.assertTrue(any("dependency_order" in error for error in errors))
        self.assertIn("gates.context must be an object", errors)
        self.assertTrue(any("reviewer_id" in error for error in errors))
        self.assertIn(
            "output_package.publication_copy must be an object",
            errors,
        )

    def test_cli_errors_use_stable_json_envelope(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(CLI_PATH),
                "--json",
                "objects",
                "get",
                "missing.object",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(3, result.returncode)
        envelope = json.loads(result.stdout)
        self.assertFalse(envelope["ok"])
        self.assertEqual("objects.get", envelope["command"])
        self.assertEqual("OBJECT_NOT_FOUND", envelope["error"]["code"])

    def test_adapter_packet_and_full_lifecycle_reach_ready(self) -> None:
        planned = build_run_plan(self.repository, self.config, self.ready_task)
        design_packet = build_adapter_packet(self.repository, planned, "design")

        self.assertEqual("design", design_packet["stage"])
        self.assertEqual(
            "schemas/content-design.schema.json",
            design_packet["required_output_schema"],
        )

        designed = apply_content_design(self.repository, planned, self.design)
        self.assertEqual("media-decided", designed["state"])

        draft_packet = build_adapter_packet(self.repository, designed, "draft")
        self.assertEqual("media-decided", draft_packet["input_state"])
        drafted = apply_artifact_record(self.repository, designed, self.draft)
        self.assertEqual("drafted", drafted["state"])

        edited = apply_artifact_record(self.repository, drafted, self.edit)
        self.assertEqual("edited", edited["state"])
        self.assertEqual(
            "produced",
            edited["output_package"]["visual_assets"]["status"],
        )

        reviewed = apply_review_record(self.repository, edited, self.review)
        self.assertEqual("reviewed", reviewed["state"])
        self.assertEqual(
            "reviewed",
            reviewed["output_package"]["visual_assets"]["status"],
        )

        ready = finalize_run(self.repository, reviewed)
        self.assertEqual("ready", ready["state"])
        self.assertEqual(
            "ready",
            ready["output_package"]["publication_copy"]["status"],
        )
        self.assertEqual([], validate_run_record(self.repository, ready))
        events = [
            entry["event"]
            for entry in ready["output_package"]["audit"]["history"]
        ]
        self.assertEqual(
            [
                "run-planned",
                "content-design-applied",
                "draft-artifact-applied",
                "edit-artifact-applied",
                "review-applied",
                "run-finalized",
            ],
            events,
        )

    def test_separate_visual_stage_blocks_review_until_assets_exist(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        run = apply_content_design(self.repository, run, self.design)
        run = apply_artifact_record(self.repository, run, self.draft)
        edit = copy.deepcopy(self.edit)
        edit["visuals"] = []
        run = apply_artifact_record(self.repository, run, edit)

        self.assertEqual("edited", run["state"])
        self.assertEqual(
            "pending-production",
            run["output_package"]["visual_assets"]["status"],
        )
        with self.assertRaises(HwrError) as raised:
            build_adapter_packet(self.repository, run, "review")
        self.assertEqual("VISUAL_PRODUCTION_INCOMPLETE", raised.exception.code)

        visual = {
            "run_id": run["run_id"],
            "artifact_revision": "artifact-2",
            "visual_revision": "visual-1",
            "items": self.edit["visuals"],
            "adapter": {
                "id": "fixture.visual-producer",
                "mode": "tool",
            },
        }
        run = apply_visual_record(self.repository, run, visual)
        self.assertEqual("produced", run["output_package"]["visual_assets"]["status"])
        self.assertEqual("review", build_adapter_packet(self.repository, run, "review")["stage"])

    def test_openai_adapter_parses_offline_design_fixture(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        updated, warnings = run_adapter_stage(
            self.repository,
            run,
            "design",
            executable=sys.executable,
            arguments=[
                str(OPENAI_ADAPTER_PATH),
                "--fixture-response",
                str(OPENAI_DESIGN_FIXTURE_PATH),
            ],
            pass_env=[],
            working_directory=str(ROOT),
        )

        self.assertEqual([], warnings)
        self.assertEqual("media-decided", updated["state"])
        self.assertTrue(
            updated["content_design"]["design_revision"].startswith(
                "openai:design:"
            )
        )

    def test_openai_adapter_produces_visual_from_offline_fixture(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        run = apply_content_design(self.repository, run, self.design)
        run = apply_artifact_record(self.repository, run, self.draft)
        edit = copy.deepcopy(self.edit)
        edit["visuals"] = []
        run = apply_artifact_record(self.repository, run, edit)

        with tempfile.TemporaryDirectory() as temporary:
            updated, warnings = run_adapter_stage(
                self.repository,
                run,
                "visual",
                executable=sys.executable,
                arguments=[
                    str(OPENAI_ADAPTER_PATH),
                    "--fixture-response",
                    str(OPENAI_VISUAL_FIXTURE_PATH),
                    "--asset-dir",
                    temporary,
                ],
                pass_env=[],
                working_directory=str(ROOT),
            )

            self.assertEqual([], warnings)
            visual = updated["output_package"]["visual_assets"]
            self.assertEqual("produced", visual["status"])
            self.assertTrue(Path(visual["items"][0]["asset"]).is_file())
            self.assertEqual("gpt-image-2", visual["items"][0]["model"])

    def test_openai_request_uses_strict_schema_without_credentials(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        packet = build_adapter_packet(self.repository, run, "design")
        args = type(
            "Args",
            (),
            {
                "text_model": "gpt-5.6-sol",
                "reasoning_effort": "medium",
                "max_output_tokens": 16000,
            },
        )()

        request = response_request(packet, "design", args)

        self.assertEqual("gpt-5.6-sol", request["model"])
        self.assertTrue(request["text"]["format"]["strict"])
        self.assertNotIn("OPENAI_API_KEY", json.dumps(request))
        schema = request["text"]["format"]["schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), set(schema["required"]))

    def test_openai_response_parser_rejects_incomplete_and_refusal(self) -> None:
        with self.assertRaises(OpenAIAdapterError):
            parse_structured_response(
                {
                    "status": "incomplete",
                    "incomplete_details": {"reason": "max_output_tokens"},
                    "output": [],
                }
            )
        with self.assertRaises(OpenAIAdapterError):
            parse_structured_response(
                {
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "content": [
                                {
                                    "type": "refusal",
                                    "refusal": "request refused",
                                }
                            ],
                        }
                    ],
                }
            )

    def test_openai_live_mode_without_allowlisted_key_fails_before_network(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        packet = build_adapter_packet(self.repository, run, "design")
        environment = os.environ.copy()
        environment.pop("OPENAI_API_KEY", None)

        result = subprocess.run(
            [sys.executable, str(OPENAI_ADAPTER_PATH), "--live"],
            cwd=ROOT,
            env=environment,
            input=json.dumps(packet),
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("--live requires OPENAI_API_KEY", result.stderr)

    def test_review_revision_loop_preserves_finding_history(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        run = apply_content_design(self.repository, run, self.design)
        run = apply_artifact_record(self.repository, run, self.draft)
        run = apply_artifact_record(self.repository, run, self.edit)

        failed_review = copy.deepcopy(self.review)
        failed_review["review_revision"] = "review-major-1"
        failed_review["readiness_candidate"] = "not-ready"
        failed_review["reviewers"][0]["status"] = "fail"
        failed_review["findings"] = [
            {
                "id": "source-001",
                "reviewer": "reviewer.source",
                "severity": "major",
                "location": "paragraph-3",
                "summary": "Qualification is too far from the design-rationale claim",
                "reason": "The inference could be read as measured effectiveness",
                "rule": "rule.source-integrity",
                "claim_ids": ["C-002"],
                "correction": "Keep the design-rationale qualification in the same sentence",
                "status": "open",
            }
        ]
        revising = apply_review_record(self.repository, run, failed_review)
        self.assertEqual("revising", revising["state"])

        revision = copy.deepcopy(self.edit)
        revision["stage"] = "revision"
        revision["artifact_revision"] = "artifact-3"
        revision["parent_revision"] = "artifact-2"
        revision["addressed_findings"] = ["source-001"]
        edited = apply_artifact_record(self.repository, revising, revision)
        self.assertEqual("edited", edited["state"])
        self.assertEqual(
            "fixed",
            edited["output_package"]["review_report"]["findings"][0]["status"],
        )
        self.assertEqual(
            "artifact-2",
            edited["output_package"]["review_report"]["artifact_revision"],
        )
        self.assertEqual(
            "artifact-3",
            edited["output_package"]["review_report"]["pending_artifact_revision"],
        )

        re_review = copy.deepcopy(failed_review)
        re_review["artifact_revision"] = "artifact-3"
        re_review["review_revision"] = "review-major-2"
        re_review["reviewers"][0]["status"] = "pass"
        re_review["findings"][0]["status"] = "fixed"
        re_review["readiness_candidate"] = "publication-ready"
        reviewed = apply_review_record(self.repository, edited, re_review)

        self.assertEqual("reviewed", reviewed["state"])
        self.assertEqual([], validate_run_record(self.repository, reviewed))

    def test_adapter_rejects_out_of_order_transition(self) -> None:
        planned = build_run_plan(self.repository, self.config, self.ready_task)

        with self.assertRaises(HwrError) as raised:
            apply_artifact_record(self.repository, planned, self.draft)

        self.assertEqual("INVALID_TRANSITION", raised.exception.code)

    def test_artifact_cannot_use_omitted_unknown_claim(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        run = apply_content_design(self.repository, run, self.design)
        draft = copy.deepcopy(self.draft)
        draft["claim_usage"].append(
            {"claim_id": "C-003", "locations": ["paragraph-5"]}
        )

        with self.assertRaises(HwrError) as raised:
            apply_artifact_record(self.repository, run, draft)

        self.assertEqual("PROHIBITED_CLAIM_USED", raised.exception.code)

    def test_subprocess_adapter_runtime_reaches_ready_without_shell(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)
        for stage in ("design", "draft", "edit", "review"):
            run, warnings = run_adapter_stage(
                self.repository,
                run,
                stage,
                executable=sys.executable,
                arguments=[str(FIXTURE_ADAPTER_PATH)],
                pass_env=[],
            )
            self.assertEqual([], warnings)
            invocation = run["output_package"]["audit"]["history"][-1][
                "adapter_runtime"
            ]
            self.assertEqual(stage, invocation["stage"])
            self.assertEqual(
                Path(sys.executable).resolve().name,
                invocation["executable"],
            )
            self.assertEqual([], invocation["passed_environment_names"])

        ready = finalize_run(self.repository, run)
        self.assertEqual("ready", ready["state"])
        self.assertEqual([], validate_run_record(self.repository, ready))

    def test_persisted_workflow_reaches_ready_through_separate_visual(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "workflow"
            result, warnings = run_editorial_workflow(
                self.repository,
                self.config,
                self.ready_task,
                workspace=workspace,
                executable=sys.executable,
                arguments=[
                    str(FIXTURE_ADAPTER_PATH),
                    "--separate-visual",
                ],
                pass_env=[],
                working_directory=str(ROOT),
            )

            self.assertEqual([], warnings)
            self.assertEqual("complete", result["status"])
            self.assertEqual("ready", result["state"])
            self.assertEqual(
                [
                    "plan",
                    "design",
                    "draft",
                    "edit",
                    "visual",
                    "review",
                    "finalize",
                ],
                [stage["stage"] for stage in result["stages"]],
            )
            for output_path in result["output_files"].values():
                self.assertTrue(Path(output_path).is_file())
            publication = Path(result["output_files"]["publication"]).read_text(
                encoding="utf-8"
            )
            self.assertIn("# Почему ограничения", publication)
            self.assertNotIn("SRC-001", publication)

    def test_persisted_workflow_stops_on_major_review_finding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result, warnings = run_editorial_workflow(
                self.repository,
                self.config,
                self.ready_task,
                workspace=Path(temporary_directory) / "workflow",
                executable=sys.executable,
                arguments=[
                    str(FIXTURE_ADAPTER_PATH),
                    "--major-review",
                ],
                pass_env=[],
                working_directory=str(ROOT),
            )

            self.assertEqual([], warnings)
            self.assertEqual("needs-revision", result["status"])
            self.assertEqual("revising", result["state"])
            self.assertEqual(1, len(result["open_findings"]))
            self.assertEqual({}, result["output_files"])

    def test_persisted_workflow_resumes_one_explicit_revision_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "workflow"
            stopped, _ = run_editorial_workflow(
                self.repository,
                self.config,
                self.ready_task,
                workspace=workspace,
                executable=sys.executable,
                arguments=[
                    str(FIXTURE_ADAPTER_PATH),
                    "--major-review",
                ],
                pass_env=[],
                working_directory=str(ROOT),
            )
            self.assertEqual("needs-revision", stopped["status"])

            resumed, warnings = resume_editorial_workflow(
                self.repository,
                workspace=workspace,
                executable=sys.executable,
                arguments=[str(FIXTURE_ADAPTER_PATH)],
                pass_env=[],
                working_directory=str(ROOT),
            )

            self.assertEqual([], warnings)
            self.assertEqual("complete", resumed["status"])
            self.assertEqual("ready", resumed["state"])
            self.assertEqual(
                ["revision", "review", "finalize"],
                [stage["stage"] for stage in resumed["stages"][-3:]],
            )
            self.assertTrue(
                Path(resumed["output_files"]["publication"]).is_file()
            )

    def test_persisted_workflow_refuses_nonempty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            (workspace / "existing.txt").write_text("keep", encoding="utf-8")

            with self.assertRaises(HwrError) as raised:
                run_editorial_workflow(
                    self.repository,
                    self.config,
                    self.ready_task,
                    workspace=workspace,
                    executable=sys.executable,
                    arguments=[str(FIXTURE_ADAPTER_PATH)],
                    pass_env=[],
                )

            self.assertEqual("WORKFLOW_DIR_NOT_EMPTY", raised.exception.code)
            self.assertEqual(
                "keep",
                (workspace / "existing.txt").read_text(encoding="utf-8"),
            )

    def test_mysticism_pilot_replays_to_valid_ready_package(self) -> None:
        config = json.loads(
            (MYSTICISM_PILOT_PATH / "config-1.0.json").read_text(
                encoding="utf-8"
            )
        )
        task = json.loads(
            (MYSTICISM_PILOT_PATH / "task.json").read_text(encoding="utf-8")
        )
        stages = {
            name: json.loads(
                (MYSTICISM_PILOT_PATH / "stages" / f"{name}.json").read_text(
                    encoding="utf-8"
                )
            )
            for name in ("design", "draft", "edit", "visual", "review")
        }

        run = build_run_plan(self.repository, config, task)
        self.assertEqual("context-ready", run["state"])
        run = apply_content_design(self.repository, run, stages["design"])
        run = apply_artifact_record(self.repository, run, stages["draft"])
        run = apply_artifact_record(self.repository, run, stages["edit"])
        self.assertEqual(
            "pending-production",
            run["output_package"]["visual_assets"]["status"],
        )
        run = apply_visual_record(self.repository, run, stages["visual"])
        run = apply_review_record(self.repository, run, stages["review"])
        run = finalize_run(self.repository, run)

        self.assertEqual("ready", run["state"])
        self.assertEqual([], validate_run_record(self.repository, run))
        self.assertEqual(
            run["output_package"]["publication_copy"]["content"].rstrip() + "\n",
            (MYSTICISM_PILOT_PATH / "result/publication.md").read_text(
                encoding="utf-8"
            ),
        )
        asset_path = ROOT / stages["visual"]["items"][0]["asset"]
        self.assertTrue(asset_path.is_file())
        self.assertEqual(
            stages["visual"]["items"][0]["sha256"],
            hashlib.sha256(asset_path.read_bytes()).hexdigest(),
        )
        saved_final = json.loads(
            (MYSTICISM_PILOT_PATH / "result/run-final.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("0.2.0-draft", saved_final["spec_revision"])
        self.assertEqual(
            [
                "run spec_revision does not match the repository",
                "run registry_revision does not match the repository",
            ],
            validate_run_record(self.repository, saved_final),
        )

    def test_persisted_workflow_stops_before_adapter_when_context_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result, warnings = run_editorial_workflow(
                self.repository,
                self.config,
                self.blocked_task,
                workspace=Path(temporary_directory) / "workflow",
                executable="adapter-that-does-not-exist",
                arguments=[],
                pass_env=[],
            )

            self.assertEqual([], warnings)
            self.assertEqual("blocked", result["status"])
            self.assertEqual("blocked", result["state"])
            self.assertTrue(result["blockers"])
            self.assertEqual(["plan"], [stage["stage"] for stage in result["stages"]])

    def test_cli_persisted_workflow_runs_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "workflow"
            result = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "workflows",
                    "run",
                    "--config",
                    str(CONFIG_PATH),
                    "--task",
                    str(READY_TASK_PATH),
                    "--workspace",
                    str(workspace),
                    "--executable",
                    sys.executable,
                    "--arg",
                    str(FIXTURE_ADAPTER_PATH),
                    "--arg=--separate-visual",
                ],
                cwd=temporary_directory,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            envelope = json.loads(result.stdout)
            self.assertTrue(envelope["ok"])
            self.assertEqual("workflows.run", envelope["command"])
            self.assertEqual("complete", envelope["data"]["status"])
            self.assertTrue(
                Path(envelope["data"]["output_files"]["publication"]).is_file()
            )

    def test_cli_persisted_workflow_resumes_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "workflow"
            start = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "workflows",
                    "run",
                    "--config",
                    str(CONFIG_PATH),
                    "--task",
                    str(READY_TASK_PATH),
                    "--workspace",
                    str(workspace),
                    "--executable",
                    sys.executable,
                    "--arg",
                    str(FIXTURE_ADAPTER_PATH),
                    "--arg=--major-review",
                ],
                cwd=temporary_directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, start.returncode, start.stderr)
            self.assertEqual(
                "needs-revision",
                json.loads(start.stdout)["data"]["status"],
            )

            resumed = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "workflows",
                    "resume",
                    "--workspace",
                    str(workspace),
                    "--executable",
                    sys.executable,
                    "--arg",
                    str(FIXTURE_ADAPTER_PATH),
                ],
                cwd=temporary_directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, resumed.returncode, resumed.stderr)
            envelope = json.loads(resumed.stdout)
            self.assertEqual("workflows.resume", envelope["command"])
            self.assertEqual("complete", envelope["data"]["status"])

    def test_subprocess_adapter_rejects_invalid_json(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)

        with self.assertRaises(HwrError) as raised:
            run_adapter_stage(
                self.repository,
                run,
                "design",
                executable=sys.executable,
                arguments=["-c", "import sys; sys.stdin.read(); print('not-json')"],
                pass_env=[],
            )

        self.assertEqual(
            "ADAPTER_OUTPUT_INVALID_JSON",
            raised.exception.code,
        )

    def test_subprocess_adapter_redacts_failed_stderr(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)

        with self.assertRaises(HwrError) as raised:
            run_adapter_stage(
                self.repository,
                run,
                "design",
                executable=sys.executable,
                arguments=[
                    "-c",
                    (
                        "import sys; sys.stdin.read(); "
                        "print('api_key=super-secret', file=sys.stderr); "
                        "raise SystemExit(7)"
                    ),
                ],
                pass_env=[],
            )

        self.assertEqual("ADAPTER_FAILED", raised.exception.code)
        self.assertNotIn("super-secret", repr(raised.exception.details))
        self.assertIn("[REDACTED]", repr(raised.exception.details))

    def test_subprocess_adapter_enforces_timeout(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)

        with self.assertRaises(HwrError) as raised:
            run_adapter_stage(
                self.repository,
                run,
                "design",
                executable=sys.executable,
                arguments=[
                    "-c",
                    "import sys,time; sys.stdin.read(); time.sleep(1)",
                ],
                pass_env=[],
                timeout_seconds=0.05,
            )

        self.assertEqual("ADAPTER_TIMEOUT", raised.exception.code)

    def test_subprocess_adapter_enforces_output_and_environment_limits(self) -> None:
        run = build_run_plan(self.repository, self.config, self.ready_task)

        with self.assertRaises(HwrError) as oversized:
            run_adapter_stage(
                self.repository,
                run,
                "design",
                executable=sys.executable,
                arguments=[
                    "-c",
                    "import sys; sys.stdin.read(); sys.stdout.write('x' * 2048)",
                ],
                pass_env=[],
                max_output_bytes=1024,
            )
        self.assertEqual("ADAPTER_OUTPUT_TOO_LARGE", oversized.exception.code)

        missing_name = "HWR_TEST_ENV_THAT_MUST_NOT_EXIST"
        self.assertNotIn(missing_name, os.environ)
        with self.assertRaises(HwrError) as missing:
            run_adapter_stage(
                self.repository,
                run,
                "design",
                executable=sys.executable,
                arguments=[str(FIXTURE_ADAPTER_PATH)],
                pass_env=[missing_name],
            )
        self.assertEqual("ADAPTER_ENV_MISSING", missing.exception.code)

    def test_cli_lifecycle_runs_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            steps = [
                (
                    [
                        "runs",
                        "plan",
                        "--config",
                        str(CONFIG_PATH),
                        "--task",
                        str(READY_TASK_PATH),
                    ],
                    temporary / "run-0.json",
                ),
                (
                    [
                        "runs",
                        "apply-design",
                        "--file",
                        str(temporary / "run-0.json"),
                        "--input",
                        str(DESIGN_PATH),
                    ],
                    temporary / "run-1.json",
                ),
                (
                    [
                        "runs",
                        "apply-artifact",
                        "--file",
                        str(temporary / "run-1.json"),
                        "--input",
                        str(DRAFT_PATH),
                    ],
                    temporary / "run-2.json",
                ),
                (
                    [
                        "runs",
                        "apply-artifact",
                        "--file",
                        str(temporary / "run-2.json"),
                        "--input",
                        str(EDIT_PATH),
                    ],
                    temporary / "run-3.json",
                ),
                (
                    [
                        "runs",
                        "apply-review",
                        "--file",
                        str(temporary / "run-3.json"),
                        "--input",
                        str(REVIEW_PATH),
                    ],
                    temporary / "run-4.json",
                ),
                (
                    [
                        "runs",
                        "finalize",
                        "--file",
                        str(temporary / "run-4.json"),
                    ],
                    temporary / "run-5.json",
                ),
            ]
            for arguments, output_path in steps:
                result = subprocess.run(
                    [
                        "python3",
                        str(CLI_PATH),
                        "--json",
                        *arguments,
                        "--out",
                        str(output_path),
                    ],
                    cwd=temporary_directory,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue(json.loads(result.stdout)["ok"])
                if output_path.name == "run-0.json":
                    packet_result = subprocess.run(
                        [
                            "python3",
                            str(CLI_PATH),
                            "--json",
                            "adapters",
                            "packet",
                            "--file",
                            str(output_path),
                            "--stage",
                            "design",
                        ],
                        cwd=temporary_directory,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        0,
                        packet_result.returncode,
                        packet_result.stderr,
                    )
                    packet = json.loads(packet_result.stdout)["data"]
                    self.assertEqual("design", packet["stage"])
                    self.assertTrue(packet["module_manifest"][0]["content"])
                    adapter_output = temporary / "adapter-run-1.json"
                    adapter_result = subprocess.run(
                        [
                            "python3",
                            str(CLI_PATH),
                            "--json",
                            "adapters",
                            "run",
                            "--file",
                            str(output_path),
                            "--stage",
                            "design",
                            "--executable",
                            sys.executable,
                            "--arg",
                            str(FIXTURE_ADAPTER_PATH),
                            "--out",
                            str(adapter_output),
                        ],
                        cwd=temporary_directory,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        0,
                        adapter_result.returncode,
                        adapter_result.stderr,
                    )
                    automated = json.loads(
                        adapter_output.read_text(encoding="utf-8")
                    )
                    self.assertEqual("media-decided", automated["state"])

            final_run = json.loads(
                (temporary / "run-5.json").read_text(encoding="utf-8")
            )
            self.assertEqual("ready", final_run["state"])

    def test_cli_smoke_runs_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "runs",
                    "plan",
                    "--config",
                    str(CONFIG_PATH),
                    "--task",
                    str(READY_TASK_PATH),
                    "--out",
                    str(Path(temporary_directory) / "run.json"),
                ],
                cwd=temporary_directory,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            envelope = json.loads(result.stdout)
            self.assertTrue(envelope["ok"])
            output_path = Path(envelope["data"]["output_file"])
            self.assertTrue(output_path.is_file())

            check_result = subprocess.run(
                [
                    "python3",
                    str(CLI_PATH),
                    "--json",
                    "runs",
                    "check",
                    "--file",
                    str(output_path),
                ],
                cwd=temporary_directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, check_result.returncode, check_result.stderr)
            check_envelope = json.loads(check_result.stdout)
            self.assertTrue(check_envelope["data"]["valid"])


if __name__ == "__main__":
    unittest.main()
