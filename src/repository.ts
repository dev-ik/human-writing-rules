import { createHash } from "node:crypto";
import { existsSync, realpathSync, statSync } from "node:fs";
import { resolve } from "node:path";

import { HwrError } from "./errors.js";
import { isObject, readJson, safeRelativePath } from "./io.js";
import type { JsonObject, ObjectEntry, Repository } from "./types.js";

export const REGISTRY_FILES = [
  "objects.json",
  "languages.json",
  "formats.json",
  "topics.json",
  "platforms.json",
  "skills.json",
  "tones.json",
  "rfcs.json",
] as const;

function sortJson(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortJson);
  }
  if (isObject(value)) {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, sortJson(value[key])]),
    );
  }
  return value;
}

function registryRevision(registriesByFile: Record<string, JsonObject>): string {
  const canonical = JSON.stringify(sortJson(registriesByFile));
  return `sha256:${createHash("sha256").update(canonical, "utf8").digest("hex")}`;
}

export function topologicalOrder(
  rootIds: string[],
  byId: Map<string, ObjectEntry>,
): string[] {
  const state = new Map<string, number>();
  const stack: string[] = [];
  const ordered: string[] = [];

  const visit = (objectId: string): void => {
    const object = byId.get(objectId);
    if (object === undefined) {
      throw new HwrError("UNKNOWN_OBJECT", `Unknown object ID: ${objectId}`);
    }
    const status = state.get(objectId) ?? 0;
    if (status === 2) return;
    if (status === 1) {
      const start = stack.indexOf(objectId);
      throw new HwrError(
        "DEPENDENCY_CYCLE",
        "Object dependency cycle detected",
        [stack.slice(start).concat(objectId)],
      );
    }
    state.set(objectId, 1);
    stack.push(objectId);
    for (const dependency of object.requires ?? []) visit(dependency);
    stack.pop();
    state.set(objectId, 2);
    ordered.push(objectId);
  };

  for (const rootId of rootIds) visit(rootId);
  return ordered;
}

export function loadRepository(rootValue: string): Repository {
  const root = resolve(rootValue);
  if (!existsSync(root) || !statSync(root).isDirectory()) {
    throw new HwrError("REPOSITORY_NOT_FOUND", `Repository not found: ${root}`);
  }
  const canonicalRoot = realpathSync(root);
  const registries: Record<string, JsonObject> = {};
  const registriesByFile: Record<string, JsonObject> = {};
  for (const filename of REGISTRY_FILES) {
    const document = readJson(resolve(canonicalRoot, "registry", filename));
    registries[filename.slice(0, -5)] = document;
    registriesByFile[filename] = document;
  }

  const rawObjects = registries.objects.objects;
  if (!Array.isArray(rawObjects)) {
    throw new HwrError(
      "INVALID_REGISTRY",
      "registry/objects.json objects must be an array",
    );
  }
  const objects: ObjectEntry[] = [];
  const byId = new Map<string, ObjectEntry>();
  rawObjects.forEach((value, index) => {
    if (!isObject(value) || typeof value.id !== "string") {
      throw new HwrError(
        "INVALID_REGISTRY",
        `registry/objects.json objects[${index}] is invalid`,
      );
    }
    if (byId.has(value.id)) {
      throw new HwrError("DUPLICATE_OBJECT", `Duplicate object ID: ${value.id}`);
    }
    if (typeof value.path !== "string") {
      throw new HwrError("INVALID_OBJECT_PATH", `${value.id}.path must be a string`);
    }
    const objectPath = safeRelativePath(canonicalRoot, value.path, `${value.id}.path`);
    if (!existsSync(objectPath) || !statSync(objectPath).isFile()) {
      throw new HwrError(
        "MISSING_OBJECT_FILE",
        `Registered object file does not exist: ${value.path}`,
      );
    }
    const entry = value as ObjectEntry;
    objects.push(entry);
    byId.set(entry.id, entry);
  });

  const specs: Record<string, string> = {
    languages: "languages",
    formats: "formats",
    topics: "topics",
    platforms: "platforms",
    skills: "skills",
    tones: "tones",
  };
  const indexes: Record<string, Map<string, JsonObject>> = {};
  for (const [registryName, collectionName] of Object.entries(specs)) {
    const collection = registries[registryName][collectionName];
    if (!Array.isArray(collection)) {
      throw new HwrError(
        "INVALID_REGISTRY",
        `registry/${registryName}.json ${collectionName} must be an array`,
      );
    }
    const index = new Map<string, JsonObject>();
    for (const value of collection) {
      if (!isObject(value) || typeof value.id !== "string") {
        throw new HwrError(
          "INVALID_REGISTRY",
          `registry/${registryName}.json contains an invalid entry`,
        );
      }
      index.set(value.id, value);
    }
    indexes[registryName] = index;
  }

  for (const object of objects) {
    if (
      object.requires !== undefined &&
      (!Array.isArray(object.requires) ||
        !object.requires.every((value) => typeof value === "string"))
    ) {
      throw new HwrError(
        "INVALID_DEPENDENCIES",
        `${object.id}.requires must be an array of object IDs`,
      );
    }
    for (const dependency of object.requires ?? []) {
      if (!byId.has(dependency)) {
        throw new HwrError(
          "UNKNOWN_DEPENDENCY",
          `${object.id} requires unknown object ${dependency}`,
        );
      }
    }
  }
  topologicalOrder([...byId.keys()], byId);

  for (const [registryName, index] of Object.entries(indexes)) {
    for (const [publicValue, entry] of index) {
      if (typeof entry.module !== "string" || !byId.has(entry.module)) {
        throw new HwrError(
          "UNKNOWN_INDEX_MODULE",
          `${registryName}.${publicValue} references unknown module ${String(entry.module)}`,
        );
      }
    }
  }

  const specRevision = registries.rfcs.version;
  if (typeof specRevision !== "string" || specRevision === "") {
    throw new HwrError(
      "INVALID_SPEC_REVISION",
      "registry/rfcs.json version must be a non-empty string",
    );
  }

  return {
    root: canonicalRoot,
    registries,
    objects,
    byId,
    indexes,
    specRevision,
    registryRevision: registryRevision(registriesByFile),
  };
}
