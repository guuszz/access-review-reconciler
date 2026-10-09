from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def _key(email: str | None) -> str:
    return (email or "").strip().casefold()


def _read_csv(path: str | Path, required: set[str]) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        missing = required - fields
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        return [{name: (value or "").strip() for name, value in row.items()} for row in reader]


def reconcile(
    people_rows: Iterable[dict[str, str]],
    account_rows: Iterable[dict[str, str]],
    exception_rows: Iterable[dict[str, str]] = (),
) -> dict[str, object]:
    active_people: dict[str, list[dict[str, str]]] = defaultdict(list)
    for person in people_rows:
        if person.get("status", "").strip().casefold() == "active":
            key = _key(person.get("email"))
            if key:
                active_people[key].append(person)

    accounts = list(account_rows)
    exception_list = list(exception_rows)
    exception_counts = Counter(_key(row.get("email")) for row in exception_list if _key(row.get("email")))
    exceptions = {_key(row.get("email")): row.get("reason", "").strip() for row in exception_list if _key(row.get("email"))}
    invalid_exceptions = [
        row for row in exception_list
        if not _key(row.get("email")) or not row.get("reason", "").strip() or exception_counts[_key(row.get("email"))] > 1
    ]
    # The same person is expected to have accounts in multiple systems. Only
    # repeated rows for the same system/account type are duplicate inventory
    # records; email alone is not an account identity across an organization.
    account_keys = [
        (
            _key(row.get("email")),
            (row.get("system") or "").strip().casefold(),
            (row.get("account_type") or "").strip().casefold(),
        )
        for row in accounts
    ]
    account_counts = Counter(account_keys)
    findings: list[dict[str, str]] = []
    exceptions_used: set[str] = set()
    for row, account_key in zip(accounts, account_keys):
        email = _key(row.get("email"))
        system = row.get("system", "").strip()
        if not email:
            kind = "missing_account_email"
        elif account_counts[account_key] > 1:
            kind = "duplicate_account_identity"
        elif len(active_people[email]) > 1:
            kind = "ambiguous_person_match"
        elif not active_people[email]:
            if email in exceptions and exceptions[email]:
                exceptions_used.add(email)
                continue
            kind = "orphan_account"
        else:
            continue
        findings.append({"finding": kind, "email": email, "system": system, "decision": "human_review_required"})

    for row in invalid_exceptions:
        findings.append({"finding": "invalid_exception", "email": _key(row.get("email")), "system": "", "decision": "human_review_required"})
    for email in exceptions.keys() - exceptions_used:
        findings.append({"finding": "stale_exception", "email": email, "system": "", "decision": "human_review_required"})

    return {
        "people_active": sum(len(rows) for rows in active_people.values()),
        "accounts_reviewed": len(accounts),
        "exceptions_documented": len(exceptions_used),
        "review_required": len(findings),
        "findings": findings,
    }


def reconcile_files(people_path: str | Path, accounts_path: str | Path, exceptions_path: str | Path | None = None) -> dict[str, object]:
    people = _read_csv(people_path, {"email", "name", "status"})
    accounts = _read_csv(accounts_path, {"email", "system", "account_type"})
    exceptions = _read_csv(exceptions_path, {"email", "reason"}) if exceptions_path else []
    return reconcile(people, accounts, exceptions)
