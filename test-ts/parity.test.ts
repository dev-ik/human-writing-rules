import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import test from "node:test";

const ROOT = process.cwd();
const NODE_CLI = resolve(ROOT, "dist/src/cli.js");
const PYTHON_CLI = resolve(ROOT, "tools/hwr.py");
const CONFIG = resolve(ROOT, "starter-kit/.human-writing-rules/config.json");
const TASK = resolve(ROOT, "examples/tasks/ru-science-article.json");
const SNAPSHOT_TASK = resolve(ROOT, "examples/source-snapshots/task.json");
const FINAL_RUN = resolve(
  ROOT,
  "examples/pilot-runs/ru-mysticism/result/run-final.json",
);

interface Invocation {
  status: number | null;
  stdout: string;
  stderr: string;
}

function invoke(executable: string, args: string[]): Invocation {
  const result = spawnSync(executable, args, {
    cwd: ROOT,
    encoding: "utf8",
  });
  if (result.error) throw result.error;
  return {
    status: result.status,
    stdout: result.stdout,
    stderr: result.stderr,
  };
}

function assertParity(args: string[]): void {
  const nodeResult = invoke(process.execPath, [NODE_CLI, ...args]);
  const pythonResult = invoke("python3", [PYTHON_CLI, ...args]);
  assert.equal(nodeResult.status, pythonResult.status, nodeResult.stderr);
  assert.deepEqual(
    JSON.parse(nodeResult.stdout),
    JSON.parse(pythonResult.stdout),
    `JSON mismatch for hwr ${args.join(" ")}`,
  );
}

test("doctor keeps the v1 JSON contract", () => {
  assertParity(["--json", "doctor"]);
});

test("registry and object discovery keep the v1 JSON contract", () => {
  assertParity(["--json", "registry", "get", "topics"]);
  assertParity([
    "--json",
    "objects",
    "list",
    "--kind",
    "reviewer",
    "--language",
    "ru",
    "--limit",
    "4",
  ]);
  assertParity(["--json", "objects", "get", "core.writing-pipeline"]);
});

test("module resolution keeps the v1 JSON contract", () => {
  assertParity([
    "--json",
    "modules",
    "resolve",
    "--config",
    CONFIG,
    "--task",
    TASK,
  ]);
});

test("agent-led questions keep the v1 JSON contract", () => {
  assertParity([
    "--json",
    "runs",
    "questions",
    "--config",
    CONFIG,
    "--limit",
    "3",
  ]);
});

test("run planning keeps the v1 JSON contract", () => {
  assertParity([
    "--json",
    "runs",
    "plan",
    "--config",
    CONFIG,
    "--task",
    TASK,
  ]);
  assertParity([
    "--json",
    "runs",
    "plan",
    "--config",
    CONFIG,
    "--task",
    SNAPSHOT_TASK,
  ]);
});

test("native errors keep their stable envelope and exit code", () => {
  assertParity(["--json", "objects", "get", "missing.object"]);
  assertParity([
    "--json",
    "runs",
    "questions",
    "--config",
    CONFIG,
    "--limit",
    "6",
  ]);
});

test("native commands do not require Python at runtime", () => {
  const result = spawnSync(process.execPath, [NODE_CLI, "--json", "doctor"], {
    cwd: ROOT,
    encoding: "utf8",
    env: { ...process.env, PATH: "" },
  });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).ok, true);
});

test("unported commands preserve the Python compatibility contract", () => {
  assertParity(["--json", "runs", "check", "--file", FINAL_RUN]);
  const help = invoke(process.execPath, [NODE_CLI, "runs", "check", "--help"]);
  assert.equal(help.status, 0, help.stderr);
  assert.match(help.stdout, /usage: hwr runs check/u);
});
