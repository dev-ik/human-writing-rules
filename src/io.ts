import { readFileSync, realpathSync, statSync } from "node:fs";
import { dirname, isAbsolute, resolve, sep } from "node:path";

import { HwrError } from "./errors.js";
import type { JsonObject } from "./types.js";

export function readJson(path: string): JsonObject {
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      throw new HwrError(
        "FILE_NOT_FOUND",
        `JSON file does not exist: ${path}`,
        [path],
      );
    }
    throw error;
  }

  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch (error) {
    throw new HwrError("INVALID_JSON", `Invalid JSON in ${path}: ${(error as Error).message}`, [
      { path },
    ]);
  }
  if (!isObject(value)) {
    throw new HwrError("INVALID_JSON_ROOT", `JSON root must be an object: ${path}`);
  }
  return value;
}

export function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export function cloneJson<T>(value: T): T {
  return structuredClone(value);
}

export function safeRelativePath(root: string, value: string, label: string): string {
  const parts = value.split(/[\\/]/u);
  if (isAbsolute(value) || parts.includes("..")) {
    throw new HwrError("UNSAFE_PATH", `${label} contains an unsafe path: ${value}`);
  }
  return resolve(root, value);
}

export function resolveSourcePath(root: string, value: unknown, label: string): string {
  if (typeof value !== "string" || value.trim() === "" || isAbsolute(value)) {
    throw new HwrError("UNSAFE_SOURCE_PATH", `${label} must be a relative path`);
  }
  const parts = value.split(/[\\/]/u);
  if (parts.includes("..")) {
    throw new HwrError(
      "UNSAFE_SOURCE_PATH",
      `${label} must remain inside the source root: ${value}`,
    );
  }

  let resolvedRoot: string;
  try {
    resolvedRoot = realpathSync(root);
  } catch {
    throw new HwrError("SOURCE_ROOT_NOT_FOUND", `Source root does not exist: ${root}`);
  }
  if (!statSync(resolvedRoot).isDirectory()) {
    throw new HwrError(
      "SOURCE_ROOT_INVALID",
      `Source root is not a directory: ${resolvedRoot}`,
    );
  }

  let resolvedPath: string;
  try {
    resolvedPath = realpathSync(resolve(resolvedRoot, value));
  } catch {
    throw new HwrError(
      "SOURCE_FILE_NOT_FOUND",
      `${label} does not exist inside the source root: ${value}`,
    );
  }
  if (resolvedPath !== resolvedRoot && !resolvedPath.startsWith(`${resolvedRoot}${sep}`)) {
    throw new HwrError(
      "UNSAFE_SOURCE_PATH",
      `${label} resolves outside the source root: ${value}`,
    );
  }
  if (!statSync(resolvedPath).isFile()) {
    throw new HwrError("SOURCE_FILE_INVALID", `${label} is not a regular file: ${value}`);
  }
  return resolvedPath;
}

export function taskSourceRoot(taskPath: string, sourceRoot?: string): string {
  return sourceRoot === undefined ? dirname(resolve(taskPath)) : resolve(sourceRoot);
}
