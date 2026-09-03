"""Cross-platform, non-production release verification for EasyCamp."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_PATHS = (
    "alembic/versions/c8b1a6f4d2e9_add_unique_external_booking_identity.py",
    "alembic/versions/f2a4c6e8b0d1_archive_houses_instead_of_deleting.py",
    "app/api/health.py",
    "app/api/site_leads.py",
    "app/avito/webhook.py",
    "app/core/security.py",
    "app/services/backup_service.py",
    "app/services/booking_service.py",
    "app/services/house_integrity_service.py",
    "app/services/house_service.py",
    "app/services/readiness_service.py",
    "app/services/sqlite_recovery.py",
    "app/services/avito_sync_service.py",
    "app/services/yandex_travel_sync_service.py",
    "tests/test_health.py",
    "tests/test_house_archiving.py",
    "tests/test_house_archiving_migration.py",
    "tests/test_house_integrity_service.py",
    "tests/test_backup_service.py",
    "tests/test_sqlite_recovery.py",
    "tests/test_booking_integrity.py",
    "tests/test_external_identity_migration.py",
    "tests/test_site_leads.py",
    "tests/test_security.py",
    "tests/test_yandex_booking_integrity.py",
    "tests/test_avito_overlap_guard.py",
)


def run(command: list[str], *, capture: bool = False) -> str:
    print(f"\n>>> {' '.join(command)}", flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    if capture:
        print(result.stdout, end="")
        return result.stdout
    return ""


def verify_python() -> None:
    python = sys.executable
    run([python, "-m", "ruff", "check", "app", "tests", "--select", "E9,F63,F7,F82"])
    run(
        [
            python,
            "-m",
            "ruff",
            "check",
            *CRITICAL_PATHS,
            "--select",
            "E,F",
            "--ignore",
            "E501,E402",
        ]
    )
    run([python, "-m", "pytest", "-q"])
    run([python, "-m", "compileall", "-q", "app", "tests"])
    run([python, "-m", "pip", "check"])

    heads_output = run([python, "-m", "alembic", "heads"], capture=True)
    heads = [line for line in heads_output.splitlines() if "(head)" in line]
    if len(heads) != 1:
        raise RuntimeError(f"Expected exactly one Alembic head, found {len(heads)}")


def verify_docker(image_tag: str) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker is required for --with-docker release verification")
    if not (ROOT / ".env").is_file():
        raise RuntimeError("docker compose config requires a local .env file")

    run(["docker", "compose", "config", "--quiet"])
    run(["docker", "build", "--tag", image_tag, "."])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="also validate Compose and build the image; required before release",
    )
    parser.add_argument("--image-tag", default="easycamp:release-check")
    args = parser.parse_args(argv)

    verify_python()
    if args.with_docker:
        verify_docker(args.image_tag)

    print("\nAll requested release checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
