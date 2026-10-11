"""Fixed-host Happy Horse API client. Paid submissions are never retried."""

from __future__ import annotations

import ipaddress
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import requests

BASE_URL = "https://api.acedata.cloud"
VIDEO_HOSTS = {"cdn.acedata.cloud", "cdn.acedata2.cloud", "platform2.cdn.acedata.cloud"}
MAX_VIDEO_BYTES = 128 * 1024 * 1024
COMPLETE = {"complete", "completed", "succeed", "succeeded", "success", "finished"}
FAILED = {"failed", "error", "cancelled", "canceled", "rejected"}
ACTION_MODELS = {
    "generate": ("happyhorse-1.1-t2v", "happyhorse-1.0-t2v"),
    "image_to_video": ("happyhorse-1.1-i2v", "happyhorse-1.0-i2v"),
    "reference_to_video": ("happyhorse-1.1-r2v", "happyhorse-1.0-r2v"),
    "video_edit": ("happyhorse-1.0-video-edit",),
}
RESOLUTIONS = ("720P", "1080P")
RATIOS = ("16:9", "9:16", "1:1", "4:3", "3:4")


class HappyHorseError(RuntimeError):
    """A customer-safe error without raw API data or credentials."""


def _credential() -> str:
    token = os.environ.get("ACEDATACLOUD_API_KEY") or os.environ.get("ACEDATACLOUD_API_TOKEN")
    if not token or not token.strip():
        raise HappyHorseError("Set ACEDATACLOUD_API_KEY in the ComfyUI process environment and restart.")
    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise HappyHorseError("Ace Data Cloud API key is empty.")
    return token


def _post(path: str, payload: dict[str, Any], *, read_only: bool = False) -> dict[str, Any]:
    token = _credential()
    for attempt in range(3 if read_only else 1):
        try:
            response = requests.post(
                BASE_URL + path, json=payload,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=(10, 60 if read_only else 45), allow_redirects=False,
            )
            break
        except requests.RequestException as exc:
            if read_only and attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise HappyHorseError(
                f"Happy Horse {'query' if read_only else 'submission'} connection failed "
                f"({type(exc).__name__}). Inspect request history before another paid submission."
            ) from None
    if not 200 <= response.status_code < 300:
        raise HappyHorseError(
            f"Ace Data Cloud returned HTTP {response.status_code}. Check access, balance, and request history."
        )
    try:
        body = response.json()
    except ValueError:
        raise HappyHorseError("Ace Data Cloud returned invalid JSON.") from None
    if not isinstance(body, dict):
        raise HappyHorseError("Ace Data Cloud returned an unexpected response.")
    if body.get("success") is False or body.get("error"):
        raise HappyHorseError("Happy Horse reported an error. Inspect its task or trace ID.")
    return body


def public_https(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("Reference media must use public HTTPS URLs.")
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.hostname
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("Reference media must use public HTTPS URLs.")
    if host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith(".local"):
        raise ValueError("Reference media must use public HTTPS URLs.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Reference media must use public HTTPS URLs.")
    return url


def parse_urls(value: str, *, maximum: int, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        if allow_empty:
            return []
        raise ValueError("Reference image URLs are required.")
    raw = value.strip()
    if raw.startswith("["):
        try:
            urls = json.loads(raw)
        except ValueError:
            raise ValueError("Reference images must be a JSON URL array or one URL per line.") from None
    else:
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
    if not isinstance(urls, list) or not all(isinstance(item, str) for item in urls):
        raise ValueError("Reference images must be a JSON URL array or one URL per line.")
    urls = list(dict.fromkeys(public_https(item) for item in urls))
    if len(urls) > maximum or (not allow_empty and not urls):
        raise ValueError(f"Use {'0–' if allow_empty else '1–'}{maximum} reference images.")
    return urls


def _result(body: dict[str, Any], *, retrieved: bool) -> Any:
    result: Any = body.get("response", body) if retrieved else body
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            result = {}
    return result or {}


def _video_urls(value: Any) -> list[str]:
    urls: list[str] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"request", "request_body", "input", "prompt"}:
                    continue
                if key == "video_url" and isinstance(child, str) and child.startswith("https://"):
                    urls.append(child)
                elif isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return list(dict.fromkeys(urls))


def _states(value: Any) -> tuple[list[str], bool]:
    states: list[str] = []
    failed = False

    def walk(item: Any) -> None:
        nonlocal failed
        if isinstance(item, dict):
            if item.get("success") is False or item.get("error"):
                failed = True
            for key, child in item.items():
                if key in {"state", "status"} and isinstance(child, str):
                    states.append(child.lower())
                elif key in {"data", "content", "task"}:
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return states, failed


def normalize(body: dict[str, Any], task_id: str = "", *, retrieved: bool = False) -> tuple[str, str, str, str]:
    result = _result(body, retrieved=retrieved)
    inner = result if isinstance(result, dict) else {}
    task_id = str(task_id or body.get("task_id") or inner.get("task_id") or body.get("id") or "")
    trace_id = str(inner.get("trace_id") or body.get("trace_id") or "")
    states, failed = _states(result)
    urls = _video_urls(result)
    unfinished = retrieved and "finished_at" in body and body["finished_at"] is None
    if (failed or any(state in FAILED for state in states)) and not unfinished:
        raise HappyHorseError("Happy Horse task failed. Inspect its task or trace ID.")
    done = not unfinished and ((states and all(state in COMPLETE for state in states)) or
                               (retrieved and body.get("finished_at")) or (urls and not states))
    if done:
        if not urls:
            raise HappyHorseError("Happy Horse task finished without a video URL.")
        return "succeeded", task_id, urls[0], trace_id
    if task_id:
        return "pending", task_id, "", trace_id
    raise HappyHorseError("No task ID or completed video was returned. Inspect request history before resubmitting.")


def submit(action: str, model: str, prompt: str, *, image_url: str = "", image_urls: str = "",
           video_url: str = "", resolution: str = "720P", ratio: str = "16:9", duration: int = 5,
           watermark: bool = False, audio_setting: str = "auto", seed: int = -1) -> tuple[str, str, str, str]:
    if action not in ACTION_MODELS or model not in ACTION_MODELS[action]:
        raise ValueError("Model does not support this Happy Horse action.")
    if resolution not in RESOLUTIONS or ratio not in RATIOS:
        raise ValueError("Unsupported Happy Horse resolution or ratio.")
    if not isinstance(duration, int) or not 3 <= duration <= 15:
        raise ValueError("Duration must be 3–15 seconds.")
    if not isinstance(seed, int) or not -1 <= seed <= 2147483647:
        raise ValueError("Seed is out of range.")
    payload: dict[str, Any] = {"action": action, "model": model, "resolution": resolution,
                               "watermark": bool(watermark), "async": True}
    if seed >= 0:
        payload["seed"] = seed
    if action in {"generate", "reference_to_video", "video_edit"} and not prompt.strip():
        raise ValueError("Prompt is required for this Happy Horse action.")
    if prompt.strip():
        payload["prompt"] = prompt.strip()
    if action in {"generate", "reference_to_video"}:
        payload.update({"ratio": ratio, "duration": duration})
    elif action == "image_to_video":
        payload["duration"] = duration
        payload["image_url"] = public_https(image_url)
    if action == "reference_to_video":
        payload["image_urls"] = parse_urls(image_urls, maximum=9)
    if action == "video_edit":
        payload["video_url"] = public_https(video_url)
        references = parse_urls(image_urls, maximum=5, allow_empty=True)
        if references:
            payload["image_urls"] = references
        if audio_setting not in {"auto", "origin"}:
            raise ValueError("Unsupported audio setting.")
        payload["audio_setting"] = audio_setting
    return normalize(_post("/happyhorse/videos", payload))


def retrieve_once(task_id: str) -> tuple[str, str, str, str]:
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("A Happy Horse task ID is required.")
    task_id = task_id.strip()
    return normalize(_post("/happyhorse/tasks", {"action": "retrieve", "id": task_id}, read_only=True),
                     task_id, retrieved=True)


def retrieve(task_id: str, wait_seconds: int) -> tuple[str, str, str, str]:
    if not isinstance(wait_seconds, int) or not 0 <= wait_seconds <= 240:
        raise ValueError("Wait seconds must be 0–240.")
    deadline = time.monotonic() + wait_seconds
    while True:
        result = retrieve_once(task_id)
        if result[0] != "pending" or time.monotonic() >= deadline:
            return result
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def retrieve_batch(task_ids_json: str) -> list[dict[str, str]]:
    try:
        ids = json.loads(task_ids_json)
    except (TypeError, ValueError):
        raise ValueError("Task IDs must be a JSON array.") from None
    if not isinstance(ids, list) or not ids or len(ids) > 20 or not all(isinstance(i, str) and i.strip() for i in ids):
        raise ValueError("Use 1–20 nonempty task IDs.")
    body = _post("/happyhorse/tasks", {"action": "retrieve_batch", "ids": ids}, read_only=True)
    items = body.get("items") or body.get("data") or []
    if not isinstance(items, list):
        raise HappyHorseError("Happy Horse returned an unexpected batch response.")
    rows: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or item.get("task_id") or "")
        try:
            status, _, video_url, trace_id = normalize(item, item_id, retrieved=True)
        except HappyHorseError:
            status, video_url, trace_id = "failed", "", ""
        rows.append({"task_id": item_id, "status": status, "video_url": video_url, "trace_id": trace_id})
    return rows


def download_video(url: str) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in VIDEO_HOSTS or parsed.username or parsed.password:
        raise HappyHorseError("Video URL must be an Ace Data Cloud HTTPS media link.")
    for attempt in range(3):
        try:
            with requests.get(url, stream=True, timeout=(10, 90), allow_redirects=False) as response:
                if response.status_code != 200:
                    raise HappyHorseError(f"Video download returned HTTP {response.status_code}.")
                claimed = int(response.headers.get("Content-Length", "0"))
                if claimed > MAX_VIDEO_BYTES:
                    raise HappyHorseError("Video exceeds the 128 MiB limit.")
                chunks: list[bytes] = []
                size = 0
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_VIDEO_BYTES:
                        raise HappyHorseError("Video exceeds the 128 MiB limit.")
                    chunks.append(chunk)
            if not size:
                raise HappyHorseError("Video download was empty.")
            return b"".join(chunks)
        except requests.RequestException as exc:
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise HappyHorseError(f"Video download failed ({type(exc).__name__}).") from None
    raise AssertionError("unreachable")
