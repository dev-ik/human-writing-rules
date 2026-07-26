export type JsonObject = Record<string, unknown>;

export interface ObjectEntry extends JsonObject {
  id: string;
  kind: string;
  path: string;
  title: string;
  requires?: string[];
  languages?: string[];
  formats?: string[];
  topics?: string[];
  platforms?: string[];
}

export interface Repository {
  root: string;
  registries: Record<string, JsonObject>;
  objects: ObjectEntry[];
  byId: Map<string, ObjectEntry>;
  indexes: Record<string, Map<string, JsonObject>>;
  specRevision: string;
  registryRevision: string;
}

export interface Resolution extends JsonObject {
  spec_revision: string;
  registry_revision: string;
  inputs: JsonObject;
  origins: Record<string, string>;
  root_objects: string[];
  dependency_order: string[];
  fallbacks: JsonObject[];
  inferences: JsonObject[];
  conflicts: JsonObject[];
  warnings: JsonObject[];
}
