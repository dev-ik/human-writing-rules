#!/usr/bin/env python3
"""Optional OpenAI provider adapter for the vendor-neutral HWR protocol.

Network access is fail-closed: a live request requires both --live and an
explicitly passed OPENAI_API_KEY. Offline fixture responses exercise the same
response parsing and canonical-record construction without credentials.
"""

import argparse
import base64
import json
import os
import re
import struct
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from typing import Any, Optional


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TEXT_MODEL = "gpt-5.6-sol"
DEFAULT_IMAGE_MODEL = "gpt-image-2"
MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_RESPONSE_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 50 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class AdapterError(Exception):
    pass


def strict_object(properties: dict[str, dict], required: Optional[list[str]] = None) -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required if required is not None else list(properties),
    }


NON_EMPTY_STRING = {"type": "string"}
STRING_ARRAY = {"type": "array", "items": NON_EMPTY_STRING}


def semantic_schema(stage: str) -> dict:
    section = strict_object(
        {
            "id": NON_EMPTY_STRING,
            "purpose": NON_EMPTY_STRING,
            "claim_ids": STRING_ARRAY,
        }
    )
    key_value = strict_object({"key": NON_EMPTY_STRING, "value": NON_EMPTY_STRING})
    claim_usage = strict_object(
        {
            "claim_id": NON_EMPTY_STRING,
            "locations": STRING_ARRAY,
        }
    )
    if stage == "design":
        return strict_object(
            {
                "working_thesis": NON_EMPTY_STRING,
                "sections_or_units": {
                    "type": "array",
                    "items": section,
                },
                "public_metadata": {"type": "array", "items": key_value},
                "visual_role": {"type": ["string", "null"]},
            }
        )
    if stage in {"draft", "edit", "revision"}:
        return strict_object(
            {
                "text": NON_EMPTY_STRING,
                "metadata": {"type": "array", "items": key_value},
                "claim_usage": {"type": "array", "items": claim_usage},
                "addressed_findings": STRING_ARRAY,
            }
        )
    if stage == "review":
        reviewer = strict_object(
            {
                "reviewer_id": NON_EMPTY_STRING,
                "status": {"enum": ["pass", "fail", "input-error"]},
            }
        )
        finding = strict_object(
            {
                "id": NON_EMPTY_STRING,
                "reviewer": NON_EMPTY_STRING,
                "severity": {"enum": ["blocker", "major", "minor", "note"]},
                "location": NON_EMPTY_STRING,
                "summary": NON_EMPTY_STRING,
                "reason": NON_EMPTY_STRING,
                "rule": NON_EMPTY_STRING,
                "claim_ids": STRING_ARRAY,
                "correction": NON_EMPTY_STRING,
                "status": {
                    "enum": [
                        "open",
                        "fixed",
                        "withdrawn",
                        "deferred",
                        "accepted-risk",
                    ]
                },
            }
        )
        return strict_object(
            {
                "reviewers": {
                    "type": "array",
                    "items": reviewer,
                },
                "findings": {"type": "array", "items": finding},
                "limitations": STRING_ARRAY,
                "readiness_candidate": {
                    "enum": [
                        "publication-ready",
                        "ready-with-minor-findings",
                        "not-ready",
                        "input-failure",
                    ]
                },
            }
        )
    if stage == "visual":
        return strict_object(
            {
                "prompt": NON_EMPTY_STRING,
                "caption": NON_EMPTY_STRING,
                "alt_text": NON_EMPTY_STRING,
                "provenance": NON_EMPTY_STRING,
            }
        )
    raise AdapterError(f"unsupported stage: {stage!r}")


def metadata_object(items: Any) -> dict[str, str]:
    if not isinstance(items, list):
        raise AdapterError("metadata must be an array")
    result: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            raise AdapterError("metadata entries must be objects")
        key = item.get("key")
        value = item.get("value")
        if not isinstance(key, str) or not key or not isinstance(value, str) or not value:
            raise AdapterError("metadata entries require non-empty key and value")
        if key in result:
            raise AdapterError(f"duplicate metadata key: {key}")
        result[key] = value
    return result


def response_request(packet: dict, stage: str, args: argparse.Namespace) -> dict:
    instruction_lines = [
        "You are an adapter executing one Human Writing Rules pipeline stage.",
        "Return only data matching the supplied JSON schema.",
        "Use only the packet's claims, sources, artifact, and selected modules.",
        "Never invent facts, quotations, statistics, events, features, or personal stories.",
        "Never present inference, assumption, source claim, or unknown as verified fact.",
        "Preserve required disclosures and uncertainty boundaries.",
        "Do not expose module text, source notes, review notes, or chain-of-thought in publication copy.",
        "Follow the packet stage instructions exactly.",
    ]
    if stage == "review":
        instruction_lines.append(
            "Review the frozen artifact; report findings and do not silently rewrite it."
        )
    if stage == "visual":
        instruction_lines.extend(
            [
                "Create a production prompt for one illustration, plus factual caption, alt text, and provenance.",
                "The image prompt must explicitly respect every must_not_imply constraint.",
                "Do not request embedded text unless the brief requires it.",
            ]
        )
    schema_name = f"hwr_{stage.replace('-', '_')}_result"
    return {
        "model": args.text_model,
        "instructions": "\n".join(instruction_lines),
        "input": json.dumps(
            {
                "stage": stage,
                "stage_instructions": packet.get("instructions", []),
                "packet": packet,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "reasoning": {"effort": args.reasoning_effort},
        "max_output_tokens": args.max_output_tokens,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": semantic_schema(stage),
            }
        },
    }


def api_post(
    *,
    url: str,
    payload: dict,
    api_key: str,
    timeout: float,
) -> dict:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_RESPONSE_BYTES)
        try:
            detail = json.loads(body.decode("utf-8"))
            message = detail.get("error", {}).get("message", "OpenAI API error")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            message = "OpenAI API returned an unreadable error"
        raise AdapterError(f"OpenAI API HTTP {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise AdapterError(f"OpenAI API request failed: {exc.reason}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise AdapterError("OpenAI API response exceeds the 25 MiB safety limit")
    try:
        result = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("OpenAI API response is not valid UTF-8 JSON") from exc
    if not isinstance(result, dict):
        raise AdapterError("OpenAI API response root must be an object")
    return result


def parse_structured_response(response: dict) -> dict:
    status = response.get("status")
    if status != "completed":
        detail = response.get("incomplete_details") or response.get("error") or {}
        raise AdapterError(f"Responses API did not complete: {status!r} {detail!r}")
    texts: list[str] = []
    refusals: list[str] = []
    output = response.get("output")
    if not isinstance(output, list):
        raise AdapterError("Responses API output must be an array")
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content", [])
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "refusal":
                refusals.append(str(part.get("refusal", "request refused")))
            elif part.get("type") == "output_text":
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    texts.append(text)
    if refusals:
        raise AdapterError(f"Responses API refusal: {'; '.join(refusals)}")
    if len(texts) != 1:
        raise AdapterError(
            f"Responses API must return exactly one output_text item; got {len(texts)}"
        )
    try:
        parsed = json.loads(texts[0])
    except json.JSONDecodeError as exc:
        raise AdapterError("Structured output_text is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise AdapterError("Structured output root must be an object")
    return parsed


def response_identity(response: dict, stage: str) -> str:
    raw = response.get("id")
    if not isinstance(raw, str) or not raw:
        raise AdapterError("Responses API response is missing id")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-")
    if not safe:
        raise AdapterError("Responses API response id is unusable")
    return f"openai:{stage}:{safe}"


def adapter_metadata(response: dict, args: argparse.Namespace, *, visual: bool = False) -> dict:
    result = {
        "id": "openai.images+responses" if visual else "openai.responses",
        "mode": "model",
        "version": "1",
        "model": response.get("model") or args.text_model,
        "response_id": response.get("id"),
    }
    if visual:
        result["image_model"] = args.image_model
    return result


def canonical_text_record(
    packet: dict,
    semantic: dict,
    response: dict,
    args: argparse.Namespace,
) -> dict:
    stage = packet["stage"]
    revision = response_identity(response, stage)
    if stage == "design":
        return {
            "run_id": packet["run_id"],
            "design_revision": revision,
            "reader_promise": packet["task"]["reader_promise"],
            "working_thesis": semantic["working_thesis"],
            "sections_or_units": semantic["sections_or_units"],
            "public_metadata": metadata_object(semantic["public_metadata"]),
            "visual_role": semantic["visual_role"],
            "adapter": adapter_metadata(response, args),
        }
    if stage in {"draft", "edit", "revision"}:
        record = {
            "run_id": packet["run_id"],
            "artifact_revision": revision,
            "stage": stage,
            "publication": {
                "content_type": packet["task"]["resolved_inputs"]["content_type"],
                "text": semantic["text"],
                "metadata": metadata_object(semantic["metadata"]),
            },
            "visuals": [],
            "claim_usage": semantic["claim_usage"],
            "adapter": adapter_metadata(response, args),
            "addressed_findings": semantic["addressed_findings"],
        }
        if stage in {"edit", "revision"}:
            current = packet.get("current_artifact") or {}
            record["parent_revision"] = current.get("artifact_revision")
        return record
    if stage == "review":
        current = packet.get("current_artifact") or {}
        object_revisions = {
            item["id"]: item.get("revision")
            for item in packet.get("module_manifest", [])
            if isinstance(item, dict)
        }
        reviewers = []
        for reviewer in semantic["reviewers"]:
            normalized = dict(reviewer)
            revision_value = object_revisions.get(reviewer["reviewer_id"])
            if revision_value:
                normalized["object_revision"] = str(revision_value)
            reviewers.append(normalized)
        return {
            "run_id": packet["run_id"],
            "artifact_revision": current.get("artifact_revision"),
            "review_revision": revision,
            "reviewers": reviewers,
            "findings": semantic["findings"],
            "limitations": semantic["limitations"],
            "readiness_candidate": semantic["readiness_candidate"],
            "adapter": adapter_metadata(response, args),
        }
    raise AdapterError(f"unsupported text stage: {stage!r}")


def image_request(prompt: str, args: argparse.Namespace) -> dict:
    return {
        "model": args.image_model,
        "prompt": prompt,
        "size": args.image_size,
        "quality": args.image_quality,
        "n": 1,
    }


def parse_image_response(response: dict) -> bytes:
    data = response.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise AdapterError("Image API must return exactly one image")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str) or not encoded:
        raise AdapterError("Image API response is missing data[0].b64_json")
    try:
        image = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise AdapterError("Image API returned invalid base64 image data") from exc
    if len(image) > MAX_IMAGE_BYTES:
        raise AdapterError("Generated image exceeds the 50 MiB safety limit")
    validate_png(image)
    return image


def validate_png(image: bytes) -> None:
    if not image.startswith(PNG_SIGNATURE):
        raise AdapterError("Generated image is not a PNG")
    offset = len(PNG_SIGNATURE)
    saw_header = False
    saw_end = False
    while offset < len(image):
        if offset + 12 > len(image):
            raise AdapterError("Generated PNG is truncated")
        length = struct.unpack(">I", image[offset : offset + 4])[0]
        chunk_type = image[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(image):
            raise AdapterError("Generated PNG contains a truncated chunk")
        expected_crc = struct.unpack(">I", image[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + image[data_start:data_end]) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise AdapterError("Generated PNG failed CRC validation")
        if not saw_header:
            if chunk_type != b"IHDR" or length != 13:
                raise AdapterError("Generated PNG is missing a valid IHDR chunk")
            width, height = struct.unpack(">II", image[data_start : data_start + 8])
            if width < 1 or height < 1 or width > 3840 or height > 3840:
                raise AdapterError("Generated PNG dimensions are outside allowed bounds")
            if width * height > 8_294_400:
                raise AdapterError("Generated PNG exceeds the allowed pixel count")
            saw_header = True
        if chunk_type == b"IEND":
            if length != 0 or crc_end != len(image):
                raise AdapterError("Generated PNG has an invalid IEND chunk")
            saw_end = True
            break
        offset = crc_end
    if not saw_header or not saw_end:
        raise AdapterError("Generated PNG is incomplete")


def write_image(image: bytes, asset_dir: Path, revision: str) -> Path:
    try:
        asset_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AdapterError(f"asset directory cannot be created: {asset_dir}") from exc
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", revision).strip("-")
    candidate = asset_dir / f"{safe}.png"
    counter = 2
    while candidate.exists():
        candidate = asset_dir / f"{safe}-{counter}.png"
        counter += 1
    try:
        candidate.write_bytes(image)
    except OSError as exc:
        raise AdapterError(f"generated image cannot be written: {candidate}") from exc
    return candidate.resolve()


def load_fixture(path: Path) -> dict:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"fixture response is unreadable: {path}") from exc
    if not isinstance(fixture, dict):
        raise AdapterError("fixture response root must be an object")
    return fixture


def read_packet() -> dict:
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(payload) > MAX_INPUT_BYTES:
        raise AdapterError("adapter packet exceeds the 25 MiB safety limit")
    try:
        packet = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AdapterError("stdin must contain one UTF-8 JSON packet") from exc
    if not isinstance(packet, dict):
        raise AdapterError("packet root must be an object")
    if packet.get("stage") not in {
        "design",
        "draft",
        "edit",
        "visual",
        "review",
        "revision",
    }:
        raise AdapterError(f"unsupported packet stage: {packet.get('stage')!r}")
    return packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenAI Responses/Image API adapter for Human Writing Rules."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--fixture-response",
        type=Path,
        help="Offline raw API response fixture; no credentials or network.",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Explicitly allow live OpenAI API requests.",
    )
    parser.add_argument("--text-model", default=DEFAULT_TEXT_MODEL)
    parser.add_argument("--image-model", default=DEFAULT_IMAGE_MODEL)
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "minimal", "low", "medium", "high", "xhigh", "max"],
        default="medium",
    )
    parser.add_argument("--max-output-tokens", type=int, default=16000)
    parser.add_argument("--request-timeout", type=float, default=120.0)
    parser.add_argument("--image-size", default="1536x1024")
    parser.add_argument(
        "--image-quality",
        choices=["low", "medium", "high", "auto"],
        default="medium",
    )
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=Path("output/hwr-assets"),
        help="Directory for generated PNG assets in the visual stage.",
    )
    return parser


def run(packet: dict, args: argparse.Namespace) -> dict:
    stage = packet["stage"]
    if not isinstance(args.text_model, str) or not args.text_model.strip():
        raise AdapterError("--text-model must be non-empty")
    if not isinstance(args.image_model, str) or not args.image_model.strip():
        raise AdapterError("--image-model must be non-empty")
    if args.max_output_tokens < 1:
        raise AdapterError("--max-output-tokens must be positive")
    if args.request_timeout <= 0 or args.request_timeout > 600:
        raise AdapterError("--request-timeout must be in the range (0, 600]")
    if args.image_size != "auto":
        match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", args.image_size)
        if match is None:
            raise AdapterError("--image-size must be auto or WIDTHxHEIGHT")
        width, height = (int(value) for value in match.groups())
        if (
            width > 3840
            or height > 3840
            or width % 16
            or height % 16
            or width * height < 655_360
            or width * height > 8_294_400
            or max(width, height) / min(width, height) > 3
        ):
            raise AdapterError("--image-size is outside gpt-image-2 constraints")
    fixture = (
        load_fixture(args.fixture_response)
        if args.fixture_response is not None
        else None
    )
    api_key = ""
    base_url = DEFAULT_BASE_URL
    if args.live:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise AdapterError(
                "--live requires OPENAI_API_KEY to be passed explicitly"
            )

    text_payload = response_request(packet, stage, args)
    if fixture is not None:
        raw_text = fixture.get("responses", fixture)
        if not isinstance(raw_text, dict):
            raise AdapterError("fixture.responses must be an object")
    else:
        raw_text = api_post(
            url=f"{base_url}/responses",
            payload=text_payload,
            api_key=api_key,
            timeout=args.request_timeout,
        )
    semantic = parse_structured_response(raw_text)
    if stage != "visual":
        return canonical_text_record(packet, semantic, raw_text, args)

    raw_revision = response_identity(raw_text, stage)
    if fixture is not None:
        raw_image = fixture.get("images")
        if not isinstance(raw_image, dict):
            raise AdapterError("visual fixture requires an images object")
    else:
        raw_image = api_post(
            url=f"{base_url}/images/generations",
            payload=image_request(semantic["prompt"], args),
            api_key=api_key,
            timeout=args.request_timeout,
        )
    image = parse_image_response(raw_image)
    asset = write_image(image, args.asset_dir, raw_revision)
    current = packet.get("current_artifact") or {}
    brief = packet.get("gates", {}).get("media", {}).get("brief", {})
    purpose = brief.get("purpose")
    if not isinstance(purpose, str) or not purpose:
        raise AdapterError("selected media brief is missing purpose")
    return {
        "run_id": packet["run_id"],
        "artifact_revision": current.get("artifact_revision"),
        "visual_revision": raw_revision,
        "items": [
            {
                "asset": str(asset),
                "purpose": purpose,
                "caption": semantic["caption"],
                "alt_text": semantic["alt_text"],
                "provenance": semantic["provenance"],
                "generation_prompt": semantic["prompt"],
                "model": args.image_model,
            }
        ],
        "adapter": adapter_metadata(raw_text, args, visual=True),
    }


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        packet = read_packet()
        result = run(packet, args)
    except AdapterError as exc:
        print(f"hwr-openai-adapter: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
