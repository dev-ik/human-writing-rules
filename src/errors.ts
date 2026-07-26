export type ErrorDetail = unknown;

export class HwrError extends Error {
  readonly code: string;
  readonly details: ErrorDetail[];

  constructor(code: string, message: string, details: ErrorDetail[] = []) {
    super(message);
    this.name = "HwrError";
    this.code = code;
    this.details = details;
  }
}

export const EXIT_BY_CODE: Readonly<Record<string, number>> = {
  INVALID_INPUT: 2,
  INVALID_LIMIT: 2,
  INVALID_TASK: 2,
  INVALID_JSON: 2,
  INVALID_JSON_ROOT: 2,
  FILE_NOT_FOUND: 2,
  OUTPUT_EXISTS: 2,
  SOURCE_ENCODING_INVALID: 2,
  SOURCE_FILE_INVALID: 2,
  SOURCE_FILE_NOT_FOUND: 2,
  SOURCE_MEDIA_TYPE_UNSUPPORTED: 2,
  SOURCE_READ_FAILED: 2,
  SOURCE_ROOT_INVALID: 2,
  SOURCE_ROOT_NOT_FOUND: 2,
  SOURCE_SNAPSHOT_INVALID: 2,
  SOURCE_SNAPSHOT_TOO_LARGE: 2,
  SOURCE_SNAPSHOT_TOTAL_TOO_LARGE: 2,
  SOURCE_TOO_LARGE: 2,
  UNSAFE_SOURCE_PATH: 2,
  RUN_INVALID: 3,
};
