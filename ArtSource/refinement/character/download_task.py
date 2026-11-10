"""Download artifacts of one successful Tripo task without submitting new work.

Only the standard library is used. Signed artifact URLs stay in memory. A saved
task response may be supplied with --task-json to avoid another task query.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import ProxyHandler, Request, build_opener


NODE = "/Users/yupeng/.nvm/versions/node/v22.22.1/bin/node"
CLI = "/Users/yupeng/.npm/_npx/f5a4b36c43527c00/node_modules/tripo-cli/dist/cli.js"
PROXY = "http://127.0.0.1:7897"
TIMEOUT = 30
RECOVERIES = 3
CHUNK = 256 * 1024


class DownloadError(RuntimeError):
    """An error safe to display without leaking a signed URL."""


def json_write(path, value):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            result.update(chunk)
    return result.hexdigest()


@contextmanager
def output_lock(output):
    output.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DownloadError("Another download is already using this output directory") from None
        yield
    finally:
        os.close(descriptor)


def sanitize(value):
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        url = urlsplit(value)
        return urlunsplit((url.scheme, url.netloc, url.path, "", ""))
    return value


def task_response(args):
    if args.task_json:
        task = json.loads(args.task_json.read_text())
    else:
        env = os.environ.copy()
        env.update(TRIPO_CLIENT_APP="codex", TRIPO_REGION="ov",
                   HTTP_PROXY=PROXY, HTTPS_PROXY=PROXY)
        result = subprocess.run(
            [NODE, CLI, "task", "get", args.task_id, "--json", "--no-open"],
            env=env, capture_output=True, text=True, timeout=90, check=False)
        if result.returncode:
            raise DownloadError(f"Task query failed with exit code {result.returncode}")
        task = json.loads(result.stdout)
    if task.get("task_id") != args.task_id:
        raise DownloadError("Task response identity does not match task_id")
    if task.get("status") != "success":
        raise DownloadError("Only an already successful task can be downloaded")
    for name in ("model_url", "rendered_image_url"):
        url = task.get("output", {}).get(name)
        if name == "rendered_image_url" and url is None:
            continue
        if not isinstance(url, str) or urlsplit(url).scheme != "https":
            raise DownloadError(f"Successful task has no valid HTTPS {name}")
    return task


def open_url(url, method="GET", headers=None):
    opener = build_opener(ProxyHandler({"http": PROXY, "https": PROXY}))
    request = Request(url, method=method, headers=headers or {})
    return opener.open(request, timeout=TIMEOUT)


def error_name(error):
    if isinstance(error, HTTPError):
        return f"HTTP {error.code}"
    return type(error).__name__


def remote_size(url):
    for attempt in range(RECOVERIES + 1):
        try:
            with open_url(url, method="HEAD") as response:
                length = int(response.headers.get("Content-Length", "0"))
                ranges = response.headers.get("Accept-Ranges", "").lower()
                if response.status != 200 or length < 12:
                    raise DownloadError("Model HEAD returned an invalid status or content length")
                if ranges != "bytes":
                    raise DownloadError("Model HEAD does not advertise byte-range downloads")
                return {"content_length": length, "accept_ranges": ranges,
                        "etag": response.headers.get("ETag")}
        except (OSError, URLError, http.client.HTTPException) as error:
            if attempt == RECOVERIES:
                raise DownloadError(f"Model HEAD failed after recovery: {error_name(error)}") from None
            time.sleep(attempt + 1)


def preview_download(url, path, temporary):
    if path.is_file():
        return
    for attempt in range(RECOVERIES + 1):
        try:
            with open_url(url) as response, temporary.open("wb") as output:
                if response.status != 200:
                    raise DownloadError("Preview download returned an invalid status")
                expected = int(response.headers.get("Content-Length", "0"))
                shutil.copyfileobj(response, output, CHUNK)
            if not temporary.stat().st_size or (expected and temporary.stat().st_size != expected):
                raise OSError("short preview response")
            temporary.replace(path)
            return
        except (OSError, URLError, http.client.HTTPException) as error:
            if attempt == RECOVERIES:
                raise DownloadError(f"Preview download failed after recovery: {error_name(error)}") from None
            time.sleep(attempt + 1)


def download_part(url, directory, index, start, end, total, etag):
    path = directory / f"{index:02d}.part"
    length = end - start + 1
    if path.exists() and path.stat().st_size > length:
        raise DownloadError(f"Part {index} is larger than its assigned range")
    attempts = 0
    for attempt in range(RECOVERIES + 1):
        completed = path.stat().st_size if path.exists() else 0
        if completed == length:
            return {"part": index, "bytes": length, "requests": attempts}
        request_start = start + completed
        try:
            headers = {"Range": f"bytes={request_start}-{end}", "Accept-Encoding": "identity"}
            if etag:
                headers["If-Range"] = etag
            attempts += 1
            with open_url(url, headers=headers) as response:
                content_range = response.headers.get("Content-Range", "")
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
                if response.status != 206 or match is None:
                    raise DownloadError(f"Part {index} did not receive a valid 206 Content-Range")
                actual_start, actual_end, actual_total = map(int, match.groups())
                if actual_start != request_start or actual_end > end or actual_end < actual_start or actual_total != total:
                    raise DownloadError(f"Part {index} received the wrong byte range")
                expected = actual_end - actual_start + 1
                if int(response.headers.get("Content-Length", str(expected))) != expected:
                    raise DownloadError(f"Part {index} has inconsistent range and length headers")
                if etag and response.headers.get("ETag", etag) != etag:
                    raise DownloadError(f"Part {index} source changed during download")
                received = 0
                with path.open("ab") as output:
                    while received < expected:
                        try:
                            chunk = response.read(min(CHUNK, expected - received))
                        except http.client.IncompleteRead as error:
                            output.write(error.partial)
                            raise
                        if not chunk:
                            break
                        output.write(chunk)
                        received += len(chunk)
            if path.stat().st_size == length:
                print(f"part {index + 1} complete ({length} bytes)", flush=True)
                return {"part": index, "bytes": length, "requests": attempts}
            raise OSError("short range response")
        except (OSError, URLError, http.client.HTTPException) as error:
            completed = path.stat().st_size if path.exists() else 0
            print(f"part {index + 1} retained {completed}/{length} bytes ({error_name(error)})", flush=True)
            if attempt == RECOVERIES:
                raise DownloadError(f"Part {index} could not finish after {RECOVERIES} recoveries") from None
            time.sleep(attempt + 1)
    raise DownloadError(f"Part {index} did not complete")


def glb_verify(path, expected):
    with path.open("rb") as stream:
        header = stream.read(12)
    if len(header) != 12:
        raise DownloadError("Downloaded model has a short GLB header")
    magic, version, declared = struct.unpack("<4sII", header)
    if magic != b"glTF" or version != 2 or declared != expected or path.stat().st_size != expected:
        raise DownloadError("Downloaded GLB header or total byte length does not match")
    return {"file": "model.glb", "bytes": expected, "sha256": digest(path),
            "glb_version": version, "glb_declared_bytes": declared}


def validate_ranges(ranges, total):
    if not isinstance(ranges, list) or not ranges:
        raise DownloadError("Saved ranges must be a nonempty list")
    cursor = 0
    for item in ranges:
        if not isinstance(item, list) or len(item) != 2:
            raise DownloadError("Each saved range must contain a start and an end")
        start, end = item
        if type(start) is not int or type(end) is not int:
            raise DownloadError("Saved range boundaries must be integers")
        if start != cursor or end < start or end >= total:
            raise DownloadError("Saved ranges overlap, have a gap or exceed the model length")
        cursor = end + 1
    if cursor != total:
        raise DownloadError("Saved ranges do not cover the complete model")


def prepare_output(task, output, preview_name):
    output.mkdir(parents=True, exist_ok=True)
    metadata = output / "task.json"
    receipt_path = output / "download_receipt.json"
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    previous = json.loads(metadata.read_text()) if metadata.exists() else None
    if any(output.iterdir()) and previous is None and receipt is None:
        raise DownloadError("Output directory is nonempty and has no matching task ownership record")
    for record in (previous, receipt):
        if record is not None and record.get("task_id") != task["task_id"]:
            raise DownloadError("Output directory belongs to a different task")
    if (output / "model.glb").exists():
        if receipt is None or receipt.get("task_id") != task["task_id"]:
            raise DownloadError("Existing model requires a matching download receipt")
        verified = glb_verify(output / "model.glb", receipt["model"]["bytes"])
        if verified["sha256"] != receipt["model"]["sha256"]:
            raise DownloadError("Existing model differs from its download receipt")
        return receipt
    safe_task = {key: sanitize(task[key]) for key in
                 ("task_id", "type", "status", "input", "created_at", "completed_at", "credits_consumed")
                 if key in task}
    safe_task["artifacts"] = {"model": "model.glb", "preview": preview_name}
    json_write(metadata, safe_task)
    return None


def download_artifacts(task, args):
    model_url = task["output"]["model_url"]
    image_url = task["output"].get("rendered_image_url")
    preview_name = None
    if image_url is not None:
        extension = Path(urlsplit(image_url).path).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise DownloadError("Preview does not have a supported image extension")
        preview_name = "preview" + extension
    output = args.output.resolve()
    existing = prepare_output(task, output, preview_name)
    if existing is not None:
        print(f"Already verified model for task {args.task_id}: {output / 'model.glb'}", flush=True)
        return
    parts = output / ".parts" / args.task_id
    parts.mkdir(parents=True, exist_ok=True)
    preview = None
    if preview_name is not None:
        preview_path = output / preview_name
        preview_download(image_url, preview_path, parts / "preview.part")
        preview = {"file": preview_name, "bytes": preview_path.stat().st_size,
                   "sha256": digest(preview_path)}
        print(f"PREVIEW_READY {preview_path}", flush=True)
    else:
        print("PREVIEW_ABSENT successful task provides no rendered image", flush=True)
    head = remote_size(model_url)
    total = head["content_length"]
    state_path = parts / "ranges.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state["task_id"] != args.task_id or state["head"] != head:
            raise DownloadError("Saved ranges belong to a different model response")
        ranges = state["ranges"]
    else:
        ranges = [[total * index // args.workers, total * (index + 1) // args.workers - 1]
                  for index in range(args.workers)]
        json_write(state_path, {"task_id": args.task_id, "head": head, "ranges": ranges})
    validate_ranges(ranges, total)
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(ranges))) as pool:
        pending = [pool.submit(download_part, model_url, parts, index, start, end, total, head["etag"])
                   for index, (start, end) in enumerate(ranges)]
        for future in as_completed(pending):
            try:
                results.append(future.result())
            except DownloadError as error:
                failures.append(str(error))
    if failures:
        raise DownloadError("; ".join(failures) + ". Partial bytes retained for the same task.")
    assembled = parts / "assembled.glb"
    with assembled.open("wb") as destination:
        for index in range(len(ranges)):
            with (parts / f"{index:02d}.part").open("rb") as source:
                shutil.copyfileobj(source, destination, CHUNK)
    model = glb_verify(assembled, total)
    receipt = {
        "task_id": args.task_id, "status": "verified", "model": model,
        "preview": preview,
        "head": head, "workers": args.workers,
        "parts": sorted(results, key=lambda item: item["part"]),
    }
    # Writing the expected receipt before publication makes a process exit
    # between these operations recoverable without adopting an unrelated GLB.
    json_write(output / "download_receipt.json", receipt)
    assembled.replace(output / "model.glb")
    shutil.rmtree(parts)
    try:
        parts.parent.rmdir()
    except OSError:
        pass
    print(f"MODEL_READY {output / 'model.glb'} {model['sha256']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--task-json", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-zA-Z0-9-]+", args.task_id):
        parser.error("task_id must contain only letters, digits and hyphens")
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    task = task_response(args)
    with output_lock(args.output.resolve()):
        download_artifacts(task, args)


if __name__ == "__main__":
    try:
        main()
    except (DownloadError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        message = str(error) if isinstance(error, DownloadError) else error_name(error)
        print(f"download failed: {message}", file=sys.stderr)
        sys.exit(1)
