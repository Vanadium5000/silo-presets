#!/usr/bin/env python3
"""Upload bounded CI evidence using Forgejo's Actions artifact protocol.

Protocol: Forgejo v15 routers/api/actions/artifacts.go (MIT).
https://forgejo.org/docs/v15.0/user/actions/advanced-features/#artifacts
Credentials come only from the current job's environment.
"""
import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import ssl
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise RuntimeError("artifact endpoint redirected; refusing to forward credentials")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("files", nargs="+", type=pathlib.Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", args.name):
        parser.error("artifact name must contain only letters, digits, dot, underscore or dash")
    run = os.environ.get("FORGEJO_RUN_ID", os.environ.get("GITHUB_RUN_ID", ""))
    if not run.isdecimal():
        raise RuntimeError("missing numeric workflow run ID")
    base = os.environ["ACTIONS_RUNTIME_URL"].rstrip("/") + "/"
    token = os.environ["ACTIONS_RUNTIME_TOKEN"]
    origin = urllib.parse.urlsplit(base)
    if origin.scheme not in ("http", "https") or not origin.hostname or origin.username:
        raise RuntimeError("invalid runtime endpoint")
    api = urllib.parse.urljoin(base, f"_apis/pipelines/workflows/{run}/artifacts")
    context = ssl.create_default_context(cafile=os.environ.get("CI_CA_FILE"))
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))

    def request(method, url, body, headers=None):
        destination = urllib.parse.urlsplit(url)
        if (destination.scheme, destination.netloc) != (origin.scheme, origin.netloc):
            raise RuntimeError("artifact endpoint changed origin")
        merged = {"Authorization": "Bearer " + token, **(headers or {})}
        req = urllib.request.Request(url, data=body, headers=merged, method=method)
        with opener.open(req, timeout=60) as response:
            return json.loads(response.read(1024 * 1024))

    names = [p.name for p in args.files]
    if len(set(names)) != len(names):
        raise RuntimeError("artifact filenames must be distinct")
    for path in args.files:
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 64 * 1024 * 1024:
            raise RuntimeError("evidence must be a nonempty regular file no larger than 64 MiB")
    upload = request("POST", api + "?api-version=6.0-preview", json.dumps({
        "Type": "actions_storage", "Name": args.name, "RetentionDays": 30
    }).encode(), {"Content-Type": "application/json"})["fileContainerResourceUrl"]
    upload = urllib.parse.urljoin(base, upload)
    for path in args.files:
        data = path.read_bytes()
        for start in range(0, len(data), 8 * 1024 * 1024):
            chunk = data[start:start + 8 * 1024 * 1024]
            url = upload + ("&" if "?" in upload else "?") + urllib.parse.urlencode({"itemPath": args.name + "/" + path.name})
            request("PUT", url, chunk, {
                "Content-Type": "application/octet-stream", "x-tfs-filelength": str(len(data)),
                "Content-Range": f"bytes {start}-{start + len(chunk) - 1}/{len(data)}",
                "x-actions-results-md5": base64.b64encode(hashlib.md5(chunk, usedforsecurity=False).digest()).decode(),
            })
    request("PATCH", api + "?" + urllib.parse.urlencode({"artifactName": args.name}), b"{}", {"Content-Type": "application/json"})
    print(f"Uploaded {len(args.files)} evidence files as {args.name}")


if __name__ == "__main__":
    main()
