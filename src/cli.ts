#!/usr/bin/env node

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

import { EXIT_BY_CODE, HwrError } from "./errors.js";
import { readJson } from "./io.js";
import {
  buildIntakePlan,
  buildRunPlan,
  doctor,
  loadTaskWithSourceSnapshots,
  resolveModules,
} from "./reference.js";
import { loadRepository } from "./repository.js";
import type { JsonObject, ObjectEntry } from "./types.js";

const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const VERSION = "1.0.0";

interface ParsedGlobal {
  repository: string;
  json: boolean;
  rest: string[];
}

interface CommandResult {
  command: string;
  data: unknown;
  warnings: unknown[];
}

function parseGlobal(argv: string[]): ParsedGlobal {
  let repository = PACKAGE_ROOT;
  let json = false;
  const rest: string[] = [];
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--json") {
      json = true;
    } else if (value === "--repo") {
      const next = argv[index + 1];
      if (next === undefined) {
        throw new HwrError("INVALID_INPUT", "--repo requires a path");
      }
      repository = resolve(next);
      index += 1;
    } else if (value.startsWith("--repo=")) {
      repository = resolve(value.slice("--repo=".length));
    } else {
      rest.push(value);
    }
  }
  return { repository, json, rest };
}

function option(
  args: string[],
  name: string,
  options: { required?: boolean; defaultValue?: string } = {},
): string | undefined {
  const exact = args.indexOf(name);
  if (exact >= 0) {
    const value = args[exact + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new HwrError("INVALID_INPUT", `${name} requires a value`);
    }
    return value;
  }
  const prefix = `${name}=`;
  const inline = args.find((value) => value.startsWith(prefix));
  if (inline !== undefined) return inline.slice(prefix.length);
  if (options.required) {
    throw new HwrError("INVALID_INPUT", `${name} is required`);
  }
  return options.defaultValue;
}

function hasFlag(args: string[], name: string): boolean {
  return args.includes(name);
}

function positional(args: string[], index: number): string | undefined {
  const values: string[] = [];
  for (let cursor = 0; cursor < args.length; cursor += 1) {
    const value = args[cursor];
    if (value.startsWith("--")) {
      if (!value.includes("=") && value !== "--force") cursor += 1;
      continue;
    }
    values.push(value);
  }
  return values[index];
}

function integerOption(
  args: string[],
  name: string,
  defaultValue: number,
): number {
  const raw = option(args, name);
  if (raw === undefined) return defaultValue;
  if (!/^-?\d+$/u.test(raw)) {
    throw new HwrError("INVALID_INPUT", `${name} must be an integer`);
  }
  return Number(raw);
}

function writeRunRecord(pathValue: string, run: JsonObject, force: boolean): JsonObject {
  const path = resolve(pathValue);
  if (existsSync(path) && !force) {
    throw new HwrError(
      "OUTPUT_EXISTS",
      `Output file already exists: ${path}`,
      ["Use --force to overwrite it."],
    );
  }
  mkdirSync(dirname(path), { recursive: true });
  const payload = `${JSON.stringify(run, null, 2)}\n`;
  writeFileSync(path, payload, "utf8");
  return {
    output_file: path,
    bytes: Buffer.byteLength(payload, "utf8"),
    run_id: run.run_id,
    state: run.state,
  };
}

function commandName(args: string[]): string {
  if (!args.length) return "unknown";
  const root = args[0];
  if (
    ["registry", "objects", "sources", "modules", "runs", "adapters", "workflows"].includes(
      root,
    ) &&
    args[1] !== undefined
  ) {
    return `${root}.${args[1]}`;
  }
  return root;
}

function isNativeCommand(args: string[]): boolean {
  const name = commandName(args);
  return [
    "doctor",
    "registry.get",
    "objects.list",
    "objects.get",
    "modules.resolve",
    "runs.questions",
    "runs.plan",
  ].includes(name);
}

function delegateToPython(argv: string[]): number {
  const result = spawnSync("python3", [resolve(PACKAGE_ROOT, "tools/hwr.py"), ...argv], {
    cwd: process.cwd(),
    encoding: "utf8",
    stdio: "inherit",
  });
  if (result.error) {
    throw new HwrError(
      "PYTHON_COMPATIBILITY_UNAVAILABLE",
      `The unported command requires Python 3: ${result.error.message}`,
      [
        "Use one of the native TypeScript commands or install Python 3 during the migration window.",
      ],
    );
  }
  return result.status ?? 3;
}

function dispatch(repositoryPath: string, args: string[]): CommandResult {
  const repository = loadRepository(repositoryPath);
  const name = commandName(args);
  const commandArgs = args.slice(name.includes(".") ? 2 : 1);
  if (name === "doctor") {
    return { command: name, data: doctor(repository), warnings: [] };
  }
  if (name === "registry.get") {
    const registryName = positional(commandArgs, 0);
    const allowed = [
      "objects",
      "languages",
      "formats",
      "topics",
      "platforms",
      "skills",
      "tones",
      "rfcs",
    ];
    if (registryName === undefined || !allowed.includes(registryName)) {
      throw new HwrError(
        "INVALID_INPUT",
        `registry name must be one of: ${allowed.join(", ")}`,
      );
    }
    return {
      command: name,
      data: repository.registries[registryName],
      warnings: [],
    };
  }
  if (name === "objects.get") {
    const objectId = positional(commandArgs, 0);
    const entry = objectId === undefined ? undefined : repository.byId.get(objectId);
    if (entry === undefined) {
      throw new HwrError("OBJECT_NOT_FOUND", `Unknown object ID: ${String(objectId)}`);
    }
    return { command: name, data: entry, warnings: [] };
  }
  if (name === "objects.list") {
    const limit = integerOption(commandArgs, "--limit", 100);
    if (limit < 1 || limit > 1000) {
      throw new HwrError("INVALID_LIMIT", "--limit must be between 1 and 1000");
    }
    const filters: Array<[keyof ObjectEntry, string | undefined]> = [
      ["kind", option(commandArgs, "--kind")],
      ["languages", option(commandArgs, "--language")],
      ["formats", option(commandArgs, "--format")],
      ["topics", option(commandArgs, "--topic")],
      ["platforms", option(commandArgs, "--platform")],
    ];
    const items = repository.objects
      .filter((entry) =>
        filters.every(([field, expected]) => {
          if (expected === undefined) return true;
          if (field === "kind") return entry.kind === expected;
          const selector = entry[field];
          return !Array.isArray(selector) || !selector.length || selector.includes(expected);
        }),
      )
      .sort((left, right) => left.id.localeCompare(right.id))
      .slice(0, limit);
    return {
      command: name,
      data: { items, count: items.length, limit },
      warnings: [],
    };
  }
  if (name === "modules.resolve") {
    const config = readJson(resolve(option(commandArgs, "--config", { required: true })!));
    const taskPath = option(commandArgs, "--task");
    const task = taskPath === undefined ? {} : readJson(resolve(taskPath));
    const resolution = resolveModules(repository, config, task);
    return {
      command: name,
      data: resolution,
      warnings: resolution.warnings,
    };
  }
  if (name === "runs.questions") {
    const config = readJson(resolve(option(commandArgs, "--config", { required: true })!));
    const taskPath = option(commandArgs, "--task");
    const sourceRoot = option(commandArgs, "--source-root");
    const task =
      taskPath === undefined
        ? { task_id: "interactive-intake" }
        : loadTaskWithSourceSnapshots(resolve(taskPath), sourceRoot);
    const data = buildIntakePlan(
      repository,
      config,
      task,
      integerOption(commandArgs, "--limit", 5),
    );
    return { command: name, data, warnings: [] };
  }
  if (name === "runs.plan") {
    const config = readJson(resolve(option(commandArgs, "--config", { required: true })!));
    const taskPath = resolve(option(commandArgs, "--task", { required: true })!);
    const sourceRoot = option(commandArgs, "--source-root");
    const run = buildRunPlan(
      repository,
      config,
      loadTaskWithSourceSnapshots(taskPath, sourceRoot),
    );
    const out = option(commandArgs, "--out");
    return {
      command: name,
      data: out === undefined ? run : writeRunRecord(out, run, hasFlag(commandArgs, "--force")),
      warnings: [],
    };
  }
  throw new HwrError("UNKNOWN_COMMAND", "Unsupported command");
}

function printHuman(command: string, data: unknown): void {
  if (command === "doctor" && typeof data === "object" && data !== null) {
    const doctorData = data as JsonObject;
    process.stdout.write(
      [
        `HWR reference runner: ${doctorData.ready ? "ready" : "not ready"}`,
        `Repository: ${String(doctorData.repository)}`,
        `Spec: ${String(doctorData.spec_revision)}`,
        `Registry: ${String(doctorData.registry_revision)}`,
        `Objects: ${String(doctorData.object_count)}`,
        "Model adapter: not configured",
      ].join("\n") + "\n",
    );
    return;
  }
  if (command === "objects.list" && typeof data === "object" && data !== null) {
    const listData = data as { items: ObjectEntry[]; count: number };
    for (const entry of listData.items) {
      process.stdout.write(`${entry.id}\t${entry.kind}\t${entry.path}\n`);
    }
    process.stderr.write(`Returned ${listData.count} object(s).\n`);
    return;
  }
  process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
}

function printHelp(): void {
  process.stdout.write(`Human Writing Rules CLI ${VERSION}

Usage:
  hwr [--repo PATH] [--json] <command>

Native TypeScript commands:
  doctor
  registry get <name>
  objects list [--kind KIND] [--language ID] [--format ID]
  objects get <object-id>
  modules resolve --config FILE [--task FILE]
  runs questions --config FILE [--task FILE] [--limit 1..5]
  runs plan --config FILE --task FILE [--out FILE] [--force]

Other v1.0 commands are delegated to the Python compatibility backend.
`);
}

export function main(argv = process.argv.slice(2)): number {
  if (
    argv.length === 0 ||
    (argv.length === 1 && (argv[0] === "--help" || argv[0] === "-h"))
  ) {
    printHelp();
    return 0;
  }
  if (
    argv.length === 1 &&
    (argv[0] === "--version" || argv[0] === "-V")
  ) {
    process.stdout.write(`${VERSION}\n`);
    return 0;
  }

  let parsed: ParsedGlobal;
  try {
    parsed = parseGlobal(argv);
  } catch (error) {
    const hwrError =
      error instanceof HwrError
        ? error
        : new HwrError("INTERNAL_ERROR", (error as Error).message);
    process.stderr.write(`error [${hwrError.code}]: ${hwrError.message}\n`);
    return EXIT_BY_CODE[hwrError.code] ?? 3;
  }

  const currentCommand = commandName(parsed.rest);
  if (!isNativeCommand(parsed.rest)) {
    try {
      return delegateToPython(argv);
    } catch (error) {
      const hwrError =
        error instanceof HwrError
          ? error
          : new HwrError("INTERNAL_ERROR", (error as Error).message);
      if (parsed.json) {
        process.stdout.write(
          `${JSON.stringify({
            ok: false,
            command: currentCommand,
            error: {
              code: hwrError.code,
              message: hwrError.message,
              details: hwrError.details,
            },
          })}\n`,
        );
      } else {
        process.stderr.write(`error [${hwrError.code}]: ${hwrError.message}\n`);
      }
      return EXIT_BY_CODE[hwrError.code] ?? 3;
    }
  }
  try {
    const result = dispatch(parsed.repository, parsed.rest);
    if (parsed.json) {
      process.stdout.write(
        `${JSON.stringify({
          ok: true,
          command: result.command,
          data: result.data,
          warnings: result.warnings,
        })}\n`,
      );
    } else {
      printHuman(result.command, result.data);
    }
    return 0;
  } catch (error) {
    const hwrError =
      error instanceof HwrError
        ? error
        : new HwrError("INTERNAL_ERROR", (error as Error).message);
    if (parsed.json) {
      process.stdout.write(
        `${JSON.stringify({
          ok: false,
          command: currentCommand,
          error: {
            code: hwrError.code,
            message: hwrError.message,
            details: hwrError.details,
          },
        })}\n`,
      );
    } else {
      process.stderr.write(`error [${hwrError.code}]: ${hwrError.message}\n`);
      for (const detail of hwrError.details) {
        process.stderr.write(`  ${String(detail)}\n`);
      }
    }
    return EXIT_BY_CODE[hwrError.code] ?? 3;
  }
}

process.exitCode = main();
