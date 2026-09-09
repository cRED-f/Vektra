#!/usr/bin/env python3
"""Load-test script for the Vektra gateway.

Fires `--concurrency` simultaneous requests at an endpoint and produces a
report: latency percentiles, throughput (req/s), and error rate.

Examples:
    # against the docker-compose backend
    python scripts/loadtest.py

    # against the kind cluster via a port-forward (tunnel into the cluster)
    python scripts/loadtest.py --url http://localhost:18000 --requests 200

    # load-test the search endpoint instead of /health (needs a token)
    python scripts/loadtest.py --endpoint /retrieve --method POST \
        --token dev-token-change-in-production
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import asdict, dataclass, field

import httpx


@dataclass
class LoadTestResult:
    """Aggregated measurements from a load-test run."""
    url: str
    endpoint: str
    concurrency: int
    total_requests: int
    duration_seconds: float
    requests_per_second: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    errors: int
    status_counts: dict = field(default_factory=dict)


async def _fire_one(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    token: str | None,
) -> tuple[float, int]:
    """Send one request and return (latency_s, status_code)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start = time.monotonic()
    resp = await client.request(method, url, headers=headers)
    latency = time.monotonic() - start
    return latency, resp.status_code


async def _worker(
    client: httpx.AsyncClient,
    url: str,
    method: str,
    token: str | None,
    semaphore: asyncio.Semaphore,
    results: list[tuple[float, int]],
):
    """Run requests, capped by the concurrency semaphore."""
    async with semaphore:
        latency, status = await _fire_one(client, url, method, token)
        results.append((latency, status))


async def run_load_test(
    url: str,
    *,
    endpoint: str,
    method: str,
    concurrency: int,
    total_requests: int,
    token: str | None,
) -> LoadTestResult:
    """Run the load test and aggregate results."""
    full_url = url.rstrip("/") + endpoint
    status_counts: dict[int, int] = {}
    results: list[tuple[float, int]] = []

    semaphore = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        start = time.monotonic()
        # Launch all requests as tasks; the semaphore caps how many run at once.
        tasks = [
            _worker(client, full_url, method, token, semaphore, results)
            for _ in range(total_requests)
        ]
        await asyncio.gather(*tasks)
        duration = time.monotonic() - start

    latencies = sorted(lat for lat, _ in results)
    for _, status in results:
        status_counts[status] = status_counts.get(status, 0) + 1

    errors = total_requests - status_counts.get(200, 0)

    def percentile(p: float) -> float:
        if not latencies:
            return 0.0
        idx = max(0, min(len(latencies) - 1, int(len(latencies) * p)))
        return latencies[idx] * 1000  # seconds -> ms

    return LoadTestResult(
        url=full_url,
        endpoint=endpoint,
        concurrency=concurrency,
        total_requests=total_requests,
        duration_seconds=round(duration, 3),
        requests_per_second=round(total_requests / duration, 1) if duration else 0.0,
        p50_ms=round(percentile(0.50), 2),
        p90_ms=round(percentile(0.90), 2),
        p95_ms=round(percentile(0.95), 2),
        p99_ms=round(percentile(0.99), 2),
        max_ms=round((latencies[-1] * 1000) if latencies else 0.0, 2),
        errors=errors,
        status_counts=status_counts,
    )


def print_report(result: LoadTestResult):
    """Pretty-print the report + write it to a JSON file."""
    print("=" * 52)
    print("  VEKTRA LOAD TEST REPORT")
    print("=" * 52)
    print(f"  target      : {result.url}")
    print(f"  concurrency : {result.concurrency}  requests: {result.total_requests}")
    print("-" * 52)
    print(f"  duration    : {result.duration_seconds}s")
    print(f"  throughput  : {result.requests_per_second} req/s")
    print(f"  p50         : {result.p50_ms} ms")
    print(f"  p90         : {result.p90_ms} ms")
    print(f"  p95         : {result.p95_ms} ms")
    print(f"  p99         : {result.p99_ms} ms")
    print(f"  max         : {result.max_ms} ms")
    print(f"  errors      : {result.errors} ({result.errors/result.total_requests:.1%})")
    print(f"  statuses    : {result.status_counts}")
    print("=" * 52)

    with open("loadtest-report.json", "w") as f:
        json.dump(asdict(result), f, indent=2)
    print("  report written to loadtest-report.json")


def main():
    parser = argparse.ArgumentParser(description="Vektra gateway load test")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="base URL of the gateway")
    parser.add_argument("--endpoint", default="/health",
                        help="path to hit (default /health)")
    parser.add_argument("--method", default="GET",
                        choices=["GET", "POST"], help="HTTP method")
    parser.add_argument("--concurrency", type=int, default=50,
                        help="simultaneous requests (default 50)")
    parser.add_argument("--requests", type=int, default=500,
                        help="total requests to send (default 500)")
    parser.add_argument("--token", default=None,
                        help="bearer token if the endpoint requires auth")
    args = parser.parse_args()

    result = asyncio.run(
        run_load_test(
            args.url,
            endpoint=args.endpoint,
            method=args.method,
            concurrency=args.concurrency,
            total_requests=args.requests,
            token=args.token,
        )
    )
    print_report(result)


if __name__ == "__main__":
    main()