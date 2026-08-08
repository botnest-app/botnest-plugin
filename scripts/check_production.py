#!/usr/bin/env python3
"""Verify public endpoints used by BotNest platform integrations."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


BASE = "https://botnest.app"


def get_json(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"GET {path} returned {response.status}")
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GET {path} returned {error.code}") from error


def expect_page(path: str) -> None:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"GET {path} returned {response.status}")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GET {path} returned {error.code}") from error


def expect_mcp_auth_challenge() -> None:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "botnest-production-check", "version": "1.0"},
            },
        }
    ).encode()
    request = urllib.request.Request(
        f"{BASE}/mcp",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        challenge = error.headers.get("WWW-Authenticate", "")
        if error.code == 401 and "resource_metadata=" in challenge:
            return
        raise RuntimeError(
            f"POST /mcp returned {error.code} without a resource metadata challenge"
        ) from error
    raise RuntimeError("POST /mcp unexpectedly allowed an unauthenticated request")


def expect_oauth_endpoint(path: str, *, method: str) -> None:
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=b"" if method == "POST" else None,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status == 404:
                raise RuntimeError(f"{method} {path} returned 404")
    except urllib.error.HTTPError as error:
        if error.code in {400, 401}:
            return
        raise RuntimeError(f"{method} {path} returned {error.code}") from error


def main(*, include_alice: bool = False) -> None:
    resource = get_json("/.well-known/oauth-protected-resource/mcp")
    if resource.get("resource") != f"{BASE}/mcp":
        raise RuntimeError("protected-resource metadata points at the wrong MCP URL")

    authorization = get_json("/.well-known/oauth-authorization-server")
    if authorization.get("issuer") != BASE:
        raise RuntimeError("authorization-server metadata has the wrong issuer")

    expect_mcp_auth_challenge()
    if include_alice:
        expect_oauth_endpoint("/oauth/alice/authorize", method="GET")
        expect_oauth_endpoint("/oauth/alice/token", method="POST")
    for path in ("/legal/privacy/", "/legal/offer/", "/legal/details/"):
        expect_page(path)
    suffix = " including Alice" if include_alice else ""
    print(f"Production review preflight passed{suffix}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-alice",
        action="store_true",
        help="Also require the confidential Yandex Alice OAuth endpoints.",
    )
    args = parser.parse_args()
    try:
        main(include_alice=args.include_alice)
    except (RuntimeError, urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Production review preflight failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
