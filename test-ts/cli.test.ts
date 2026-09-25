import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

const ROOT = process.cwd();
const NODE_CLI = resolve(ROOT, "dist/src/cli.js");
const PACKAGE_VERSION = JSON.parse(
  readFileSync(resolve(ROOT, "package.json"), "utf8"),
).version;

test("CLI version and help report the installed distribution outside the repository", () => {
  const directory = mkdtempSync(join(tmpdir(), "hwr-cli-version-"));
  try {
    writeFileSync(join(directory, "package.json"), '{"version":"99.0.0"}\n');
    for (const args of [["--version"], ["-V"], ["--help"], ["-h"], []]) {
      const result = spawnSync(process.execPath, [NODE_CLI, ...args], {
        cwd: directory,
        encoding: "utf8",
        env: { ...process.env, PATH: "" },
      });
      assert.equal(result.status, 0, result.stderr);
      const expected = ["--version", "-V"].includes(args[0] ?? "")
        ? PACKAGE_VERSION
        : `Human Writing Rules CLI ${PACKAGE_VERSION}`;
      assert.equal(result.stdout.split("\n")[0], expected);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
