import { createHash } from "node:crypto";
import { readFileSync, realpathSync, statSync } from "node:fs";
import { dirname, relative, resolve, sep } from "node:path";

import { HwrError } from "./errors.js";
import {
  cloneJson,
  isObject,
  readJson,
  resolveSourcePath,
  taskSourceRoot,
} from "./io.js";
import { topologicalOrder } from "./repository.js";
import type { JsonObject, Repository, Resolution } from "./types.js";

const SPEC_SCHEMA_VERSION = "1.0";
const SOURCE_SNAPSHOT_SCHEMA =
  "https://human-writing-rules.example/schemas/source-snapshot.schema.json";
const SOURCE_SNAPSHOT_VERSION = "1.0";
const MAX_SOURCE_SNAPSHOT_BYTES = 2 * 1024 * 1024;
const MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES =
  MAX_SOURCE_SNAPSHOT_BYTES + 256 * 1024;
const MAX_SOURCE_SNAPSHOT_TOTAL_BYTES = 8 * 1024 * 1024;

const ALLOWED_PERSPECTIVES = new Set([
  "editorial",
  "first-person",
  "expert",
  "reporter",
  "neutral",
]);
const ALLOWED_RISK_LEVELS = new Set(["low", "medium", "high"]);
const ALLOWED_VISUAL_MODES = new Set(["none", "auto", "required"]);
const ALLOWED_CLAIM_CLASSIFICATIONS = new Set([
  "verified-fact",
  "source-claim",
  "opinion",
  "inference",
  "assumption",
  "unknown",
]);
const ALLOWED_CLAIM_DISPOSITIONS = new Set([
  "use",
  "narrow",
  "attribute",
  "research",
  "omit",
]);
const ALLOWED_SOURCE_MEDIA_TYPES = new Set([
  "application/json",
  "application/xml",
  "text/csv",
  "text/html",
  "text/markdown",
  "text/plain",
]);
const ALLOWED_ASSESSMENTS: Record<string, Set<string>> = {
  source_freshness: new Set(["adequate", "inadequate", "unknown", "not-applicable"]),
  platform_constraints: new Set(["known", "unknown", "not-applicable"]),
  perspective: new Set(["authorized", "unauthorized", "unknown", "not-applicable"]),
  rights: new Set(["cleared", "blocked", "unknown", "not-applicable"]),
};

const REQUIRED_ROOTS = [
  "core.writing-pipeline",
  "core.content-model",
  "core.context-selection",
  "rule.source-integrity",
  "rule.human-signals.core",
  "reviewer.source",
  "reviewer.language",
  "reviewer.human-signals",
  "reviewer.editor",
];

const REVIEW_ORDER = [
  "reviewer.source",
  "reviewer.topic",
  "reviewer.format",
  "reviewer.language",
  "reviewer.human-signals",
  "reviewer.platform",
  "reviewer.visual",
  "reviewer.editor",
];

function nonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim() !== "";
}

function asObject(value: unknown): JsonObject {
  return isObject(value) ? value : {};
}

function appendUnique(values: string[], value: string): void {
  if (!values.includes(value)) values.push(value);
}

function valueWithOrigin(
  config: JsonObject,
  task: JsonObject,
  field: string,
): [unknown, string] {
  if (field in task && task[field] !== null) return [task[field], "task"];
  if (field in config && config[field] !== null) return [config[field], "config"];
  return [null, "missing"];
}

export function validateConfig(config: JsonObject): string[] {
  const errors: string[] = [];
  for (const field of ["version", "spec_revision", "language", "content_type"]) {
    if (!nonEmptyString(config[field])) errors.push(`${field} must be a non-empty string`);
  }
  if (
    config.author_perspective !== undefined &&
    config.author_perspective !== null &&
    !ALLOWED_PERSPECTIVES.has(String(config.author_perspective))
  ) {
    errors.push("author_perspective is invalid");
  }
  if (
    config.risk_level !== undefined &&
    config.risk_level !== null &&
    !ALLOWED_RISK_LEVELS.has(String(config.risk_level))
  ) {
    errors.push("risk_level is invalid");
  }
  const visuals = config.visuals ?? {};
  if (!isObject(visuals)) {
    errors.push("visuals must be an object");
  } else if (!ALLOWED_VISUAL_MODES.has(String(visuals.mode ?? "auto"))) {
    errors.push("visuals.mode must be none, auto, or required");
  }
  const reviewers = config.reviewers ?? [];
  if (
    !Array.isArray(reviewers) ||
    !reviewers.every((item) => nonEmptyString(item))
  ) {
    errors.push("reviewers must be an array of object IDs");
  } else if (new Set(reviewers).size !== reviewers.length) {
    errors.push("reviewers must not contain duplicates");
  }
  return errors;
}

export function validateSourceSnapshot(
  snapshot: unknown,
  expectedSourceId?: string,
): string[] {
  if (!isObject(snapshot)) return ["snapshot must be an object"];
  const errors: string[] = [];
  const allowedFields = new Set([
    "$schema",
    "schema_version",
    "snapshot_id",
    "source_id",
    "media_type",
    "origin",
    "captured_at",
    "sha256",
    "bytes",
    "content",
    "rights",
    "notes",
  ]);
  const extra = Object.keys(snapshot)
    .filter((key) => !allowedFields.has(key))
    .sort();
  if (extra.length) errors.push(`snapshot contains unknown fields: ${extra.join(", ")}`);
  if ((snapshot.$schema ?? SOURCE_SNAPSHOT_SCHEMA) !== SOURCE_SNAPSHOT_SCHEMA) {
    errors.push("snapshot $schema is not the source-snapshot schema");
  }
  if (snapshot.schema_version !== SOURCE_SNAPSHOT_VERSION) {
    errors.push(`snapshot schema_version must be '${SOURCE_SNAPSHOT_VERSION}'`);
  }
  for (const field of ["snapshot_id", "source_id", "media_type", "sha256", "content"]) {
    if (typeof snapshot[field] !== "string") {
      errors.push(`snapshot ${field} must be a string`);
    }
  }
  for (const field of ["snapshot_id", "source_id"]) {
    if (typeof snapshot[field] === "string" && snapshot[field].trim() === "") {
      errors.push(`snapshot ${field} must not be empty`);
    }
  }
  if (expectedSourceId !== undefined && snapshot.source_id !== expectedSourceId) {
    errors.push(
      `snapshot source_id ${JSON.stringify(snapshot.source_id)} does not match ${JSON.stringify(expectedSourceId)}`,
    );
  }
  if (
    typeof snapshot.media_type === "string" &&
    !ALLOWED_SOURCE_MEDIA_TYPES.has(snapshot.media_type)
  ) {
    errors.push(`snapshot media_type is unsupported: '${snapshot.media_type}'`);
  }
  if (!isObject(snapshot.origin)) {
    errors.push("snapshot origin must be an object");
  } else {
    if (Object.keys(snapshot.origin).some((key) => !["kind", "path"].includes(key))) {
      errors.push("snapshot origin contains unknown fields");
    }
    if (snapshot.origin.kind !== "local-file") {
      errors.push("snapshot origin.kind must be 'local-file'");
    }
    const originPath = snapshot.origin.path;
    if (!nonEmptyString(originPath)) {
      errors.push("snapshot origin.path must be a non-empty relative path");
    } else if (
      originPath.startsWith("/") ||
      originPath.split(/[\\/]/u).includes("..")
    ) {
      errors.push("snapshot origin.path must be a safe relative path");
    }
  }
  if (
    snapshot.captured_at !== undefined &&
    snapshot.captured_at !== null &&
    !nonEmptyString(snapshot.captured_at)
  ) {
    errors.push("snapshot captured_at must be a non-empty string when present");
  }
  for (const field of ["rights", "notes"]) {
    if (
      snapshot[field] !== undefined &&
      snapshot[field] !== null &&
      typeof snapshot[field] !== "string"
    ) {
      errors.push(`snapshot ${field} must be a string when present`);
    }
  }
  const byteCount = snapshot.bytes;
  if (
    !Number.isInteger(byteCount) ||
    typeof byteCount !== "number" ||
    byteCount < 0 ||
    byteCount > MAX_SOURCE_SNAPSHOT_BYTES
  ) {
    errors.push(
      `snapshot bytes must be an integer between 0 and ${MAX_SOURCE_SNAPSHOT_BYTES}`,
    );
  }
  if (typeof snapshot.content === "string") {
    if (snapshot.content.includes("\0")) {
      errors.push("snapshot content must not contain NUL bytes");
    }
    const encoded = Buffer.from(snapshot.content, "utf8");
    if (encoded.length > MAX_SOURCE_SNAPSHOT_BYTES) {
      errors.push(`snapshot content exceeds ${MAX_SOURCE_SNAPSHOT_BYTES} bytes`);
    }
    if (typeof byteCount === "number" && byteCount !== encoded.length) {
      errors.push("snapshot bytes does not match UTF-8 content length");
    }
    const digest = `sha256:${createHash("sha256").update(encoded).digest("hex")}`;
    if (snapshot.sha256 !== digest) {
      errors.push("snapshot sha256 does not match content");
    }
  }
  return errors;
}

export function validateTaskRecord(task: JsonObject): string[] {
  const errors: string[] = [];
  if (!nonEmptyString(task.task_id)) errors.push("task_id must be a non-empty string");
  for (const field of [
    "language",
    "locale",
    "content_type",
    "topic",
    "platform",
    "skill",
    "tone",
    "author_perspective",
    "risk_level",
  ]) {
    if (field in task && task[field] !== null && !nonEmptyString(task[field])) {
      errors.push(`${field} must be a non-empty string when present`);
    }
  }

  const assessments = task.assessments ?? {};
  const assessmentObject = isObject(assessments) ? assessments : {};
  if (!isObject(assessments)) errors.push("assessments must be an object");
  for (const [name, allowed] of Object.entries(ALLOWED_ASSESSMENTS)) {
    const value = String(assessmentObject[name] ?? "unknown");
    if (!allowed.has(value)) errors.push(`assessments.${name} is invalid: '${value}'`);
  }

  const sources = task.sources ?? [];
  const sourceList = Array.isArray(sources) ? sources : [];
  if (!Array.isArray(sources)) errors.push("sources must be an array");
  const sourceIds = new Set<string>();
  const snapshotIds = new Set<string>();
  let totalSnapshotBytes = 0;
  sourceList.forEach((source, index) => {
    const label = `sources[${index}]`;
    if (!isObject(source)) {
      errors.push(`${label} must be an object`);
      return;
    }
    for (const field of ["id", "title", "role"]) {
      if (!nonEmptyString(source[field])) {
        errors.push(`${label}.${field} must be a non-empty string`);
      }
    }
    if (typeof source.id === "string") {
      if (sourceIds.has(source.id)) errors.push(`duplicate source ID: ${source.id}`);
      sourceIds.add(source.id);
    }
    if (source.snapshot_path !== undefined && !nonEmptyString(source.snapshot_path)) {
      errors.push(`${label}.snapshot_path must be a non-empty string`);
    }
    if (source.snapshot_path !== undefined && source.snapshot !== undefined) {
      errors.push(`${label} must not define both snapshot and snapshot_path`);
    }
    if (source.snapshot !== undefined) {
      errors.push(
        ...validateSourceSnapshot(
          source.snapshot,
          typeof source.id === "string" ? source.id : undefined,
        ).map((message) => `${label}.${message}`),
      );
      if (isObject(source.snapshot)) {
        if (typeof source.snapshot.snapshot_id === "string") {
          if (snapshotIds.has(source.snapshot.snapshot_id)) {
            errors.push(`duplicate snapshot ID: ${source.snapshot.snapshot_id}`);
          }
          snapshotIds.add(source.snapshot.snapshot_id);
        }
        if (typeof source.snapshot.bytes === "number") {
          totalSnapshotBytes += source.snapshot.bytes;
        }
      }
    }
  });
  if (totalSnapshotBytes > MAX_SOURCE_SNAPSHOT_TOTAL_BYTES) {
    errors.push(
      `source snapshots exceed ${MAX_SOURCE_SNAPSHOT_TOTAL_BYTES} total bytes`,
    );
  }

  const claims = task.claims ?? [];
  const claimList = Array.isArray(claims) ? claims : [];
  if (!Array.isArray(claims)) errors.push("claims must be an array");
  const claimIds = new Set<string>();
  claimList.forEach((claim, index) => {
    const label = `claims[${index}]`;
    if (!isObject(claim)) {
      errors.push(`${label} must be an object`);
      return;
    }
    for (const field of ["id", "text", "classification", "disposition"]) {
      if (!nonEmptyString(claim[field])) {
        errors.push(`${label}.${field} must be a non-empty string`);
      }
    }
    if (typeof claim.id === "string") {
      if (claimIds.has(claim.id)) errors.push(`duplicate claim ID: ${claim.id}`);
      claimIds.add(claim.id);
    }
    if (!ALLOWED_CLAIM_CLASSIFICATIONS.has(String(claim.classification))) {
      errors.push(`${label}.classification is invalid`);
    }
    if (!ALLOWED_CLAIM_DISPOSITIONS.has(String(claim.disposition))) {
      errors.push(`${label}.disposition is invalid`);
    }
    if (typeof (claim.material ?? true) !== "boolean") {
      errors.push(`${label}.material must be boolean`);
    }
    const supporting = claim.source_ids ?? [];
    if (
      !Array.isArray(supporting) ||
      !supporting.every((item) => nonEmptyString(item))
    ) {
      errors.push(`${label}.source_ids must be an array of source IDs`);
    } else {
      for (const sourceId of supporting) {
        if (!sourceIds.has(sourceId)) {
          errors.push(`${label} references unknown source ${sourceId}`);
        }
      }
    }
  });
  const media = task.media ?? {};
  if (!isObject(media)) {
    errors.push("media must be an object");
  } else if (!["pending", "none", "selected", "blocked"].includes(String(media.decision ?? "pending"))) {
    errors.push("media.decision is invalid");
  }
  return errors;
}

export function resolveModules(
  repository: Repository,
  config: JsonObject,
  task: JsonObject = {},
): Resolution {
  const structuralErrors = validateConfig(config).concat(
    Object.keys(task).length ? validateTaskRecord(task) : [],
  );
  if (structuralErrors.length) {
    throw new HwrError(
      "INVALID_INPUT",
      "Config or task record is structurally invalid",
      structuralErrors,
    );
  }
  if (config.spec_revision !== repository.specRevision) {
    throw new HwrError(
      "SPEC_REVISION_MISMATCH",
      "Config spec_revision does not match registry/rfcs.json",
      [{ config: config.spec_revision, repository: repository.specRevision }],
    );
  }
  if (
    config.registry_revision !== undefined &&
    config.registry_revision !== repository.registryRevision
  ) {
    throw new HwrError(
      "REGISTRY_REVISION_MISMATCH",
      "Config registry_revision does not match the current registry digest",
      [{ config: config.registry_revision, repository: repository.registryRevision }],
    );
  }

  const inputs: JsonObject = {};
  const origins: Record<string, string> = {};
  const fallbacks: JsonObject[] = [];
  const inferences: JsonObject[] = [];
  const warnings: JsonObject[] = [];
  const roots = [...REQUIRED_ROOTS];

  let [language, origin] = valueWithOrigin(config, task, "language");
  if (typeof language !== "string" || !repository.indexes.languages.has(language)) {
    throw new HwrError("UNKNOWN_LANGUAGE", `Unknown language: ${JSON.stringify(language)}`);
  }
  inputs.language = language;
  origins.language = origin;
  appendUnique(roots, String(repository.indexes.languages.get(language)?.module));

  let [locale, localeOrigin] = valueWithOrigin(config, task, "locale");
  if (locale === null) {
    locale = repository.indexes.languages.get(language)?.default_locale;
    localeOrigin = "inferred";
    inferences.push({
      field: "locale",
      value: locale,
      reason: `default locale for language ${language}`,
    });
  }
  inputs.locale = locale;
  origins.locale = localeOrigin;

  let [contentType, contentOrigin] = valueWithOrigin(config, task, "content_type");
  if (
    typeof contentType !== "string" ||
    !repository.indexes.formats.has(contentType)
  ) {
    throw new HwrError(
      "UNKNOWN_CONTENT_TYPE",
      `Unknown content_type: ${JSON.stringify(contentType)}`,
    );
  }
  inputs.content_type = contentType;
  origins.content_type = contentOrigin;
  appendUnique(roots, String(repository.indexes.formats.get(contentType)?.module));
  appendUnique(roots, "reviewer.format");

  let [topic, topicOrigin] = valueWithOrigin(config, task, "topic");
  if (typeof topic !== "string" || !repository.indexes.topics.has(topic)) {
    const fallback = repository.registries.topics.fallback;
    if (typeof fallback !== "string" || !repository.indexes.topics.has(fallback)) {
      throw new HwrError("TOPIC_FALLBACK_MISSING", "Topic fallback is invalid");
    }
    fallbacks.push({
      field: "topic",
      input: topic,
      value: fallback,
      reason: "unknown or missing topic",
    });
    topic = fallback;
    topicOrigin = "fallback";
  }
  const resolvedTopic = String(topic);
  inputs.topic = resolvedTopic;
  origins.topic = topicOrigin;
  appendUnique(
    roots,
    String(repository.indexes.topics.get(resolvedTopic)?.module),
  );
  appendUnique(roots, "reviewer.topic");

  let [platform, platformOrigin] = valueWithOrigin(config, task, "platform");
  if (typeof platform !== "string" || !repository.indexes.platforms.has(platform)) {
    const generic = contentType === "article" ? "blog" : "social";
    fallbacks.push({
      field: "platform",
      input: platform,
      value: generic,
      reason: `generic platform for format ${contentType}`,
    });
    platform = generic;
    platformOrigin = platformOrigin === "missing" ? "inferred" : "fallback";
  }
  const resolvedPlatform = String(platform);
  const platformEntry = repository.indexes.platforms.get(resolvedPlatform)!;
  if (platformEntry.default_format !== contentType) {
    throw new HwrError(
      "PLATFORM_FORMAT_CONFLICT",
      `Platform ${resolvedPlatform} is incompatible with content_type ${contentType}`,
      [
        {
          platform_default_format: platformEntry.default_format,
          content_type: contentType,
        },
      ],
    );
  }
  inputs.platform = resolvedPlatform;
  origins.platform = platformOrigin;
  appendUnique(roots, String(platformEntry.module));
  appendUnique(roots, "reviewer.platform");

  const [skill, skillOrigin] = valueWithOrigin(config, task, "skill");
  if (skill !== null) {
    if (typeof skill !== "string" || !repository.indexes.skills.has(skill)) {
      throw new HwrError("UNKNOWN_SKILL", `Unknown skill: ${JSON.stringify(skill)}`);
    }
    inputs.skill = skill;
    origins.skill = skillOrigin;
    appendUnique(roots, String(repository.indexes.skills.get(skill)?.module));
  } else {
    inputs.skill = null;
    origins.skill = "omitted";
  }

  const [tone, toneOrigin] = valueWithOrigin(config, task, "tone");
  if (tone !== null) {
    if (typeof tone !== "string" || !repository.indexes.tones.has(tone)) {
      throw new HwrError("UNKNOWN_TONE", `Unknown tone: ${JSON.stringify(tone)}`);
    }
    inputs.tone = tone;
    origins.tone = toneOrigin;
    appendUnique(roots, String(repository.indexes.tones.get(tone)?.module));
  } else {
    inputs.tone = null;
    origins.tone = "omitted";
    inferences.push({
      field: "register",
      value: "direct-neutral",
      reason: "no tone module selected",
    });
  }

  for (const field of ["audience", "intent", "author_perspective"]) {
    const [value, valueOrigin] = valueWithOrigin(config, task, field);
    inputs[field] = value;
    origins[field] = valueOrigin;
  }
  if (
    inputs.author_perspective !== null &&
    !ALLOWED_PERSPECTIVES.has(String(inputs.author_perspective))
  ) {
    throw new HwrError(
      "UNKNOWN_AUTHOR_PERSPECTIVE",
      `Unknown author perspective: ${JSON.stringify(inputs.author_perspective)}`,
    );
  }

  let [riskLevel, riskOrigin] = valueWithOrigin(config, task, "risk_level");
  if (riskLevel === null) {
    riskLevel =
      repository.indexes.topics.get(resolvedTopic)?.default_risk ?? "low";
    riskOrigin = "inferred";
    inferences.push({
      field: "risk_level",
      value: riskLevel,
      reason: `default risk for topic ${resolvedTopic}`,
    });
  }
  if (typeof riskLevel !== "string" || !ALLOWED_RISK_LEVELS.has(riskLevel)) {
    throw new HwrError(
      "UNKNOWN_RISK_LEVEL",
      `Unknown risk level: ${JSON.stringify(riskLevel)}`,
    );
  }
  inputs.risk_level = riskLevel;
  origins.risk_level = riskOrigin;

  const visuals = task.visuals ?? config.visuals ?? {};
  if (!isObject(visuals)) {
    throw new HwrError("INVALID_VISUAL_CONFIG", "visuals must be an object");
  }
  const visualMode = String(visuals.mode ?? "auto");
  if (!ALLOWED_VISUAL_MODES.has(visualMode)) {
    throw new HwrError("UNKNOWN_VISUAL_MODE", `Unknown visual mode: ${visualMode}`);
  }
  inputs.visual_mode = visualMode;
  origins.visual_mode =
    "visuals" in task ? "task" : "visuals" in config ? "config" : "inferred";
  if (visualMode === "auto" || visualMode === "required") {
    appendUnique(roots, "rule.visual-integrity");
    appendUnique(roots, "reviewer.visual");
  }

  const reviewers = task.reviewers ?? config.reviewers ?? [];
  if (!Array.isArray(reviewers)) {
    throw new HwrError("INVALID_REVIEWERS", "reviewers must be an array");
  }
  for (const reviewerId of reviewers) {
    const reviewer =
      typeof reviewerId === "string" ? repository.byId.get(reviewerId) : undefined;
    if (reviewer === undefined || reviewer.kind !== "reviewer") {
      throw new HwrError(
        "UNKNOWN_REVIEWER",
        `Unknown reviewer object: ${String(reviewerId)}`,
      );
    }
    appendUnique(roots, reviewerId as string);
  }

  const dependencyOrder = topologicalOrder(roots, repository.byId);
  for (const objectId of roots) {
    const object = repository.byId.get(objectId)!;
    for (const [selectorName, selectedValue] of [
      ["languages", language],
      ["formats", contentType],
      ["topics", resolvedTopic],
      ["platforms", resolvedPlatform],
    ] as const) {
      const selector = object[selectorName];
      if (
        Array.isArray(selector) &&
        selector.length &&
        !selector.includes(String(selectedValue))
      ) {
        throw new HwrError(
          "OBJECT_APPLICABILITY_ERROR",
          `${objectId} excludes ${selectorName}=${selectedValue}`,
        );
      }
    }
  }

  return {
    spec_revision: repository.specRevision,
    registry_revision: repository.registryRevision,
    inputs,
    origins,
    root_objects: roots,
    dependency_order: dependencyOrder,
    fallbacks,
    inferences,
    conflicts: [],
    warnings,
  };
}

function blocker(
  code: string,
  field: string,
  message: string,
  remediation: string,
): JsonObject {
  return { code, field, message, remediation };
}

function buildContextGate(
  config: JsonObject,
  task: JsonObject,
  resolution: Resolution,
): JsonObject {
  const blockers: JsonObject[] = [];
  const inputs = resolution.inputs;
  const requiredContext: JsonObject = {
    subject: task.subject,
    reader_promise: task.reader_promise,
    audience: inputs.audience,
    intent: inputs.intent,
    author_perspective: inputs.author_perspective,
  };
  for (const [field, value] of Object.entries(requiredContext)) {
    if (
      value === undefined ||
      value === null ||
      value === "" ||
      (Array.isArray(value) && value.length === 0)
    ) {
      blockers.push(
        blocker(
          "MISSING_CONTEXT",
          field,
          `Required context is missing: ${field}`,
          `Provide ${field} before drafting.`,
        ),
      );
    }
  }
  if (inputs.content_type === "article" && !task.central_question) {
    blockers.push(
      blocker(
        "MISSING_CENTRAL_QUESTION",
        "central_question",
        "An article needs a central reader question.",
        "Provide the question the article must answer.",
      ),
    );
  }
  const assessments = asObject(task.assessments);
  const perspective = inputs.author_perspective;
  if (
    (perspective === "first-person" || perspective === "expert") &&
    (assessments.perspective ?? "unknown") !== "authorized"
  ) {
    blockers.push(
      blocker(
        "UNAUTHORIZED_PERSPECTIVE",
        "assessments.perspective",
        `${perspective} perspective is not verified as authorized.`,
        "Supply authorized author material or choose a legitimate perspective.",
      ),
    );
  }
  const sourceConfig = asObject(config.sources);
  const sourceRequired = sourceConfig.required === true;
  const sources = Array.isArray(task.sources) ? task.sources : [];
  if (sourceRequired && !sources.length) {
    blockers.push(
      blocker(
        "MISSING_REQUIRED_SOURCES",
        "sources",
        "The config requires sources but the task contains none.",
        "Add source records or change the task scope.",
      ),
    );
  }
  const freshness = assessments.source_freshness ?? "unknown";
  if (
    (sourceRequired || sources.length > 0) &&
    freshness !== "adequate" &&
    freshness !== "not-applicable"
  ) {
    blockers.push(
      blocker(
        "SOURCE_FRESHNESS_UNRESOLVED",
        "assessments.source_freshness",
        `Source freshness is ${freshness}.`,
        "Assess the source set against the task cutoff.",
      ),
    );
  }
  const platformAssessment = assessments.platform_constraints ?? "unknown";
  if (
    platformAssessment !== "known" &&
    platformAssessment !== "not-applicable"
  ) {
    blockers.push(
      blocker(
        "PLATFORM_CONSTRAINTS_UNRESOLVED",
        "assessments.platform_constraints",
        "Material platform constraints have not been assessed.",
        "Verify current platform constraints or mark them not applicable.",
      ),
    );
  }
  const claims = Array.isArray(task.claims) ? task.claims : [];
  if (!claims.length) {
    blockers.push(
      blocker(
        "EMPTY_CLAIM_LEDGER",
        "claims",
        "The task contains no planned claims.",
        "Add at least one classified planned claim.",
      ),
    );
  }
  for (const rawClaim of claims) {
    if (!isObject(rawClaim)) continue;
    if (rawClaim.material === false || rawClaim.disposition === "omit") continue;
    const claimId = String(rawClaim.id);
    const classification = rawClaim.classification;
    const sourceIds = Array.isArray(rawClaim.source_ids) ? rawClaim.source_ids : [];
    if (
      (classification === "verified-fact" || classification === "source-claim") &&
      sourceIds.length === 0
    ) {
      blockers.push(
        blocker(
          "UNSUPPORTED_MATERIAL_CLAIM",
          `claims.${claimId}`,
          `Material ${classification} claim has no supporting source.`,
          "Add source IDs, narrow, research, or omit the claim.",
        ),
      );
    }
    if (
      (classification === "inference" || classification === "assumption") &&
      !rawClaim.qualification
    ) {
      blockers.push(
        blocker(
          "UNQUALIFIED_NONFACTUAL_CLAIM",
          `claims.${claimId}`,
          `Material ${classification} lacks a qualification.`,
          "Expose the reasoning or limitation, narrow, or omit the claim.",
        ),
      );
    }
    if (
      classification === "unknown" &&
      rawClaim.disposition !== "research" &&
      rawClaim.disposition !== "omit"
    ) {
      blockers.push(
        blocker(
          "UNKNOWN_CLAIM_SELECTED",
          `claims.${claimId}`,
          "An unknown claim cannot be selected for drafting.",
          "Research or omit the claim.",
        ),
      );
    }
    if (rawClaim.disposition === "research") {
      blockers.push(
        blocker(
          "RESEARCH_REQUIRED",
          `claims.${claimId}`,
          "A material claim still requires research.",
          "Complete research, reclassify, narrow, or omit the claim.",
        ),
      );
    }
  }
  return {
    gate: "context-gate",
    status: blockers.length ? "blocked" : "pass",
    blockers,
    checked_claims: claims.length,
    checked_sources: sources.length,
  };
}

function buildMediaDecision(
  config: JsonObject,
  task: JsonObject,
  resolution: Resolution,
): JsonObject {
  const mode = String(resolution.inputs.visual_mode);
  const media = asObject(task.media);
  let decision = String(media.decision ?? "pending");
  let reason = media.reason ?? null;
  const findings: JsonObject[] = [];
  if (mode === "none") {
    if (decision === "selected") {
      findings.push(
        blocker(
          "VISUAL_MODE_CONFLICT",
          "media.decision",
          "A selected asset conflicts with visuals.mode=none.",
          "Change visual mode or remove the selected asset.",
        ),
      );
    } else {
      decision = "none";
      reason = reason ?? "Visual production is disabled by config.";
    }
  }
  if (mode === "required" && decision === "none") {
    findings.push(
      blocker(
        "REQUIRED_VISUAL_OMITTED",
        "media.decision",
        "Visual mode is required but the media decision is none.",
        "Select a supportable asset or mark the visual gate blocked.",
      ),
    );
  }
  if (decision === "selected") {
    const brief = media.brief;
    if (!isObject(brief)) {
      findings.push(
        blocker(
          "MISSING_VISUAL_BRIEF",
          "media.brief",
          "Selected media needs a visual brief.",
          "Provide the visual purpose, evidence boundary, handoff, and acceptance criteria.",
        ),
      );
    } else {
      for (const field of [
        "purpose",
        "reader_benefit",
        "evidence_basis",
        "must_not_imply",
        "asset_type",
        "acceptance_criteria",
      ]) {
        const value = brief[field];
        if (
          value === undefined ||
          value === null ||
          value === "" ||
          (Array.isArray(value) && value.length === 0)
        ) {
          findings.push(
            blocker(
              "INCOMPLETE_VISUAL_BRIEF",
              `media.brief.${field}`,
              `Selected media brief is missing ${field}.`,
              `Provide media.brief.${field}.`,
            ),
          );
        }
      }
    }
    const rights = asObject(task.assessments).rights ?? "unknown";
    if (rights !== "cleared" && rights !== "not-applicable") {
      findings.push(
        blocker(
          "VISUAL_RIGHTS_UNRESOLVED",
          "assessments.rights",
          `Visual rights assessment is ${rights}.`,
          "Clear rights or select a supportable alternative.",
        ),
      );
    }
  }
  if (decision === "blocked") {
    findings.push(
      blocker(
        "VISUAL_GATE_BLOCKED",
        "media.decision",
        typeof reason === "string" && reason
          ? reason
          : "The visual gate is explicitly blocked.",
        "Resolve the visual blocker or omit the asset when mode permits.",
      ),
    );
  }
  const status = findings.length
    ? "blocked"
    : decision === "pending"
      ? "pending"
      : "ready";
  return {
    mode,
    decision,
    status,
    reason,
    brief: media.brief ?? null,
    findings,
  };
}

function buildReviewPlan(
  repository: Repository,
  resolution: Resolution,
): JsonObject[] {
  const selected = new Set(
    resolution.root_objects.filter(
      (objectId) => repository.byId.get(objectId)?.kind === "reviewer",
    ),
  );
  const ordered = REVIEW_ORDER.filter((reviewerId) => selected.has(reviewerId));
  for (const reviewerId of [...selected].sort()) {
    if (!ordered.includes(reviewerId)) ordered.push(reviewerId);
  }
  return ordered.map((reviewerId) => ({
    reviewer_id: reviewerId,
    title: repository.byId.get(reviewerId)?.title,
    status: "pending",
  }));
}

export function buildRunPlan(
  repository: Repository,
  config: JsonObject,
  task: JsonObject,
): JsonObject {
  const taskErrors = validateTaskRecord(task);
  if (taskErrors.length) {
    throw new HwrError(
      "INVALID_TASK",
      "Task record is structurally invalid",
      taskErrors,
    );
  }
  const resolution = resolveModules(repository, config, task);
  const contextGate = buildContextGate(config, task, resolution);
  const mediaDecision = buildMediaDecision(config, task, resolution);
  let state = "context-ready";
  let blockedStage: string | null = null;
  if (contextGate.status === "blocked") {
    state = "blocked";
    blockedStage = "context-gate";
  } else if (mediaDecision.status === "blocked") {
    state = "blocked";
    blockedStage = "visual-gate";
  }
  const blockers = (contextGate.blockers as JsonObject[]).concat(
    mediaDecision.findings as JsonObject[],
  );
  const nextActions = blockers.length
    ? blockers.map((item) => String(item.remediation))
    : ["Create the content design from the reader promise and claim ledger."];
  if (!blockers.length) {
    if (mediaDecision.decision === "pending") {
      nextActions.push("Complete the media decision before visual production.");
    } else if (mediaDecision.decision === "selected") {
      nextActions.push(
        "Produce or commission the selected asset from the approved brief.",
      );
    }
    nextActions.push("Draft for meaning, then run the declared review plan.");
  }
  const visualOutputStatus =
    mediaDecision.status === "blocked"
      ? "blocked"
      : mediaDecision.decision === "pending"
        ? "pending"
        : mediaDecision.decision === "selected"
          ? "planned"
          : "not-applicable";

  const sourceFields = [
    "id",
    "title",
    "role",
    "location",
    "publication_date",
    "retrieved_at",
    "version",
    "status",
    "scope",
    "rights",
    "notes",
    "snapshot",
  ];
  const sources = (Array.isArray(task.sources) ? task.sources : [])
    .filter(isObject)
    .map((source) =>
      Object.fromEntries(
        sourceFields
          .filter((field) => source[field] !== undefined && source[field] !== null)
          .map((field) => [field, source[field]]),
      ),
    );
  const sourceNotes = cloneJson(sources).map((source) => {
    if (isObject(source.snapshot)) {
      source.snapshot = Object.fromEntries(
        Object.entries(source.snapshot).filter(([key]) => key !== "content"),
      );
    }
    return source;
  });
  const revision = String(task.revision ?? "1");
  return {
    schema_version: SPEC_SCHEMA_VERSION,
    run_id: `${String(task.task_id)}:${revision}`,
    task_id: task.task_id,
    task_revision: revision,
    spec_revision: repository.specRevision,
    registry_revision: repository.registryRevision,
    state,
    blocked_stage: blockedStage,
    task: {
      subject: task.subject ?? null,
      central_question: task.central_question ?? null,
      reader_promise: task.reader_promise ?? null,
      primary_job: task.primary_job ?? null,
      artifact_form: task.artifact_form ?? null,
      resolved_inputs: resolution.inputs,
      constraints: task.constraints ?? config.constraints ?? [],
      required_disclosures: task.required_disclosures ?? [],
    },
    resolution,
    sources,
    claim_ledger: task.claims ?? [],
    gates: {
      framing: { status: "pass" },
      module_resolution: { status: "pass" },
      context: contextGate,
      media: mediaDecision,
    },
    content_design: {
      status: state !== "blocked" ? "pending" : "blocked",
      reader_promise: task.reader_promise ?? null,
      working_thesis: null,
      sections_or_units: [],
    },
    review_plan: buildReviewPlan(repository, resolution),
    output_package: {
      publication_copy: { status: "not-started", content: null },
      visual_assets: { status: visualOutputStatus, items: [] },
      source_notes: {
        status: "prepared",
        sources: sourceNotes,
        unresolved_claims: (Array.isArray(task.claims) ? task.claims : [])
          .filter(
            (claim) =>
              isObject(claim) &&
              (claim.classification === "unknown" || claim.disposition === "research"),
          )
          .map((claim) => (claim as JsonObject).id),
      },
      review_report: { status: "not-started", findings: [] },
      revision_summary: { status: "not-started", changes: [] },
      audit: {
        status: "prepared",
        fallbacks: resolution.fallbacks,
        inferences: resolution.inferences,
        deviations: [],
        history: [
          {
            event: "run-planned",
            from_state: null,
            to_state: state,
            record_revision: task.revision ?? "1",
          },
        ],
      },
    },
    blockers,
    next_actions: [...new Set(nextActions)],
  };
}

function intakeQuestion(
  id: string,
  field: string,
  prompt: string,
  why: string,
  answerFormat: string,
  options: string[] = [],
): JsonObject {
  return {
    id,
    field,
    prompt,
    why,
    required: true,
    blocks_drafting: true,
    answer_format: answerFormat,
    options,
  };
}

function renderIntakeAudience(value: unknown, language: string): string {
  if (typeof value === "string") return value;
  if (isObject(value)) {
    const parts: string[] = [];
    if (nonEmptyString(value.description)) parts.push(value.description);
    if (nonEmptyString(value.knowledge_level)) {
      parts.push(
        `${language === "ru" ? "уровень" : "knowledge level"}: ${value.knowledge_level}`,
      );
    }
    if (Array.isArray(value.needs)) {
      const rendered = value.needs.filter(nonEmptyString).join("; ");
      if (rendered) {
        parts.push(
          `${language === "ru" ? "задачи читателя" : "reader needs"}: ${rendered}`,
        );
      }
    }
    if (parts.length) return parts.join("; ");
  }
  return JSON.stringify(value);
}

export function buildIntakePlan(
  repository: Repository,
  config: JsonObject,
  task: JsonObject,
  limit = 5,
): JsonObject {
  if (!Number.isInteger(limit) || limit < 1 || limit > 5) {
    throw new HwrError("INVALID_LIMIT", "--limit must be between 1 and 5");
  }
  const run = buildRunPlan(repository, config, task);
  const resolution = run.resolution as Resolution;
  const inputs = resolution.inputs;
  const origins = resolution.origins;
  const language = inputs.language === "ru" ? "ru" : "en";
  const questions: JsonObject[] = [];
  const agentActions: JsonObject[] = [];
  const consumed = new Set<string>();
  const key = (code: unknown, field: unknown): string => `${String(code)}\0${String(field)}`;
  const actionOverrides = new Map<string, string>([
    [
      key("MISSING_CONTEXT", "reader_promise"),
      "Derive a bounded reader promise after the subject, audience, and intent are confirmed.",
    ],
    [
      key("SOURCE_FRESHNESS_UNRESOLVED", "assessments.source_freshness"),
      "Assess source freshness against the task cutoff after sources are available.",
    ],
    [
      key("PLATFORM_CONSTRAINTS_UNRESOLVED", "assessments.platform_constraints"),
      "Verify current platform constraints or mark them not applicable.",
    ],
    [
      key("EMPTY_CLAIM_LEDGER", "claims"),
      "Build and classify the planned claim ledger from the resolved brief and source set.",
    ],
  ]);
  const addQuestion = (question: JsonObject): void => {
    if (!questions.some((item) => item.id === question.id)) questions.push(question);
  };

  if (!task.subject) {
    addQuestion(
      intakeQuestion(
        "Q-SUBJECT",
        "subject",
        language === "ru"
          ? "О чём именно нужно написать: какой объект, событие, произведение, вопрос или тезис является предметом материала?"
          : "What exactly should the piece cover: which object, event, work, question, or claim is its subject?",
        language === "ru"
          ? "Без точного предмета нельзя определить тезис и нужные источники."
          : "The thesis and required sources depend on the exact subject.",
        "free-text",
      ),
    );
    consumed.add(key("MISSING_CONTEXT", "subject"));
  }
  if (origins.audience === "config" || origins.intent === "config") {
    const audience = renderIntakeAudience(inputs.audience, language);
    const intent = String(inputs.intent ?? "");
    addQuestion(
      intakeQuestion(
        "Q-AUDIENCE-INTENT",
        "audience,intent",
        language === "ru"
          ? `Сейчас предполагаются аудитория ${audience} и цель «${intent}». Подтвердите их или уточните, для кого пишем и что читатель должен понять, почувствовать или сделать.`
          : `The current defaults assume audience ${audience} and intent “${intent}”. Confirm them or clarify who this is for and what the reader should understand, feel, or do.`,
        language === "ru"
          ? "Аудитория и результат для читателя определяют глубину, структуру и язык материала."
          : "Audience and reader outcome determine depth, structure, and language.",
        "confirm-or-correct",
        ["confirm", "change", "agent-choice"],
      ),
    );
  }
  if (inputs.content_type === "article" && !task.central_question) {
    addQuestion(
      intakeQuestion(
        "Q-CENTRAL-QUESTION",
        "central_question",
        language === "ru"
          ? "На какой главный вопрос читателя должна ответить статья?"
          : "What central reader question must the article answer?",
        language === "ru"
          ? "Главный вопрос удерживает границы статьи и не даёт подменить материал общими рассуждениями."
          : "The central question bounds the article and prevents generic filler.",
        "free-text",
      ),
    );
    consumed.add(key("MISSING_CENTRAL_QUESTION", "central_question"));
  }
  const confirmable = [
    "language",
    "content_type",
    "topic",
    "platform",
    "skill",
    "tone",
    "author_perspective",
    "risk_level",
    "visual_mode",
  ];
  const proposedDefaults = Object.fromEntries(
    confirmable
      .filter((field) => origins[field] === "config" && inputs[field] !== null)
      .map((field) => [field, inputs[field]]),
  );
  if (Object.keys(proposedDefaults).length) {
    const rendered = Object.entries(proposedDefaults)
      .map(([field, value]) => `${field}=${String(value)}`)
      .join(", ");
    addQuestion(
      intakeQuestion(
        "Q-EDITORIAL-DEFAULTS",
        Object.keys(proposedDefaults).join(","),
        language === "ru"
          ? `Подтвердите рабочие настройки: ${rendered}. Можно перечислить изменения или ответить «выбери сам».`
          : `Confirm these working defaults: ${rendered}. List changes or answer “use your judgment”.`,
        language === "ru"
          ? "Эти значения взяты из конфигурации проекта, а не из текущего задания."
          : "These values come from project configuration, not from the current task.",
        "confirm-or-correct",
        ["confirm", "change", "agent-choice"],
      ),
    );
  }

  const blockers = run.blockers as JsonObject[];
  const blockerKeys = new Set(blockers.map((item) => key(item.code, item.field)));
  if (blockerKeys.has(key("MISSING_REQUIRED_SOURCES", "sources"))) {
    addQuestion(
      intakeQuestion(
        "Q-SOURCE-PLAN",
        "sources",
        language === "ru"
          ? "Какие источники уже есть? Если их нет, можно ли агенту самостоятельно найти актуальные источники, или нужно сузить материал до предоставленных данных?"
          : "Which sources are already available? If there are none, may the agent research current sources, or should the piece be limited to supplied material?",
        language === "ru"
          ? "Конфигурация требует источники, а в задании их пока нет."
          : "The configuration requires sources, but the task has none.",
        "choice-and-free-text",
        ["provide-sources", "authorize-research", "narrow-scope"],
      ),
    );
    consumed.add(key("MISSING_REQUIRED_SOURCES", "sources"));
  }

  for (const item of blockers) {
    const itemKey = key(item.code, item.field);
    if (consumed.has(itemKey)) continue;
    if (item.code === "UNAUTHORIZED_PERSPECTIVE") {
      addQuestion(
        intakeQuestion(
          "Q-AUTHOR-PERSPECTIVE",
          String(item.field),
          language === "ru"
            ? "Есть ли подтверждённый личный опыт или экспертные материалы автора? Если нет, выбрать редакционную или нейтральную позицию?"
            : "Is authorized first-person experience or expert material available? If not, should the piece use an editorial or neutral perspective?",
          String(item.message),
          "choice-and-free-text",
          ["supply-author-material", "editorial", "neutral"],
        ),
      );
      continue;
    }
    if (
      ["VISUAL_MODE_CONFLICT", "REQUIRED_VISUAL_OMITTED", "VISUAL_GATE_BLOCKED"].includes(
        String(item.code),
      )
    ) {
      addQuestion(
        intakeQuestion(
          "Q-VISUAL-DECISION",
          String(item.field),
          language === "ru"
            ? "Иллюстрация обязательна, опциональна или не нужна? Если обязательна, какую задачу она должна решать?"
            : "Is a visual required, optional, or unnecessary? If required, what job must it perform?",
          String(item.message),
          "choice-and-free-text",
          ["required", "auto", "none"],
        ),
      );
      continue;
    }
    if (item.code === "VISUAL_RIGHTS_UNRESOLVED") {
      addQuestion(
        intakeQuestion(
          "Q-VISUAL-RIGHTS",
          String(item.field),
          language === "ru"
            ? "Какие права, согласия, бренды, персонажи или реальные люди нужно учитывать для иллюстрации?"
            : "Which rights, permissions, brands, characters, or real people must the visual account for?",
          String(item.message),
          "free-text",
        ),
      );
      continue;
    }
    agentActions.push({
      code: item.code,
      field: item.field,
      action: actionOverrides.get(itemKey) ?? item.remediation,
      reason: item.message,
    });
  }
  const batch = questions.slice(0, limit);
  return {
    schema_version: "1.0",
    task_id: run.task_id,
    spec_revision: run.spec_revision,
    registry_revision: run.registry_revision,
    status: questions.length
      ? "questions-required"
      : agentActions.length
        ? "agent-action-required"
        : "ready",
    question_batch: batch,
    questions_total: questions.length,
    remaining_question_count: Math.max(0, questions.length - batch.length),
    agent_actions: agentActions,
    proposed_defaults: proposedDefaults,
    instructions: [
      "Ask only the current question batch and wait for the answers.",
      "Do not repeat answered questions or ask the user to perform research, claim classification, or registry work the agent can do.",
      "Treat “use your judgment” as authority to choose only within the stated scope and integrity constraints.",
      "Update the task record after every answer, then regenerate questions before drafting.",
    ],
  };
}

export function loadTaskWithSourceSnapshots(
  taskPath: string,
  sourceRoot?: string,
): JsonObject {
  const task = readJson(taskPath);
  const root = taskSourceRoot(taskPath, sourceRoot);
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
  const hydrated = cloneJson(task);
  let totalBytes = 0;
  const sources = Array.isArray(hydrated.sources) ? hydrated.sources : [];
  sources.forEach((rawSource, index) => {
    if (!isObject(rawSource)) return;
    let snapshot = rawSource.snapshot;
    if (rawSource.snapshot_path !== undefined && snapshot !== undefined) {
      throw new HwrError(
        "SOURCE_SNAPSHOT_INVALID",
        `sources[${index}] must not define both snapshot and snapshot_path`,
      );
    }
    if (rawSource.snapshot_path !== undefined) {
      const snapshotFile = resolveSourcePath(
        resolvedRoot,
        rawSource.snapshot_path,
        `sources[${index}].snapshot_path`,
      );
      const payload = readFileSync(snapshotFile);
      if (payload.length > MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES) {
        throw new HwrError(
          "SOURCE_SNAPSHOT_TOO_LARGE",
          `Snapshot document exceeds ${MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES} bytes`,
          [{ path: snapshotFile }],
        );
      }
      let snapshotText: string;
      try {
        snapshotText = new TextDecoder("utf-8", { fatal: true }).decode(payload);
      } catch {
        throw new HwrError(
          "SOURCE_ENCODING_INVALID",
          `sources[${index}].snapshot_path must be UTF-8 JSON`,
        );
      }
      try {
        snapshot = JSON.parse(snapshotText);
      } catch (error) {
        throw new HwrError(
          "INVALID_JSON",
          `Invalid JSON in sources[${index}].snapshot_path: ${(error as Error).message}`,
          [{ path: snapshotFile }],
        );
      }
      if (!isObject(snapshot)) {
        throw new HwrError(
          "INVALID_JSON_ROOT",
          `JSON root must be an object: sources[${index}].snapshot_path`,
        );
      }
      rawSource.snapshot = snapshot;
      delete rawSource.snapshot_path;
    }
    if (snapshot === undefined) return;
    const errors = validateSourceSnapshot(
      snapshot,
      typeof rawSource.id === "string" ? rawSource.id : undefined,
    );
    if (errors.length) {
      throw new HwrError(
        "SOURCE_SNAPSHOT_INVALID",
        `sources[${index}] has an invalid snapshot`,
        errors,
      );
    }
    totalBytes += Number((snapshot as JsonObject).bytes);
    if (totalBytes > MAX_SOURCE_SNAPSHOT_TOTAL_BYTES) {
      throw new HwrError(
        "SOURCE_SNAPSHOT_TOTAL_TOO_LARGE",
        `Source snapshots exceed ${MAX_SOURCE_SNAPSHOT_TOTAL_BYTES} bytes`,
        [{ bytes: totalBytes, limit: MAX_SOURCE_SNAPSHOT_TOTAL_BYTES }],
      );
    }
  });
  return hydrated;
}

export function doctor(repository: Repository): JsonObject {
  return {
    ready: true,
    mode: "offline",
    auth_required: false,
    repository: repository.root,
    spec_revision: repository.specRevision,
    registry_revision: repository.registryRevision,
    object_count: repository.objects.length,
    indexes: Object.fromEntries(
      Object.entries(repository.indexes).map(([name, entries]) => [
        name,
        entries.size,
      ]),
    ),
    capabilities: [
      "registry-read",
      "generated-registry-index",
      "benchmark-runner",
      "reviewed-example-coverage",
      "release-verification",
      "visual-benchmark-acceptance",
      "object-discovery",
      "module-resolution",
      "local-source-snapshots",
      "context-gate",
      "agent-led-intake",
      "claim-ledger-check",
      "media-decision-check",
      "review-plan",
      "adapter-packets",
      "visual-production-stage",
      "subprocess-adapter-runtime",
      "persisted-editorial-workflow",
      "lifecycle-transitions",
      "readiness-gate",
      "run-record-validation",
    ],
    model_adapter: "not-configured",
    provider_adapters: [
      {
        id: "openai.responses+images",
        status: "available-not-configured",
        network_default: "disabled",
      },
    ],
  };
}

export function repositoryRelativePath(root: string, path: string): string {
  return relative(root, resolve(path)).split(sep).join("/");
}
