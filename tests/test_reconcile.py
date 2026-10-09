from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from access_review.reconcile import reconcile, reconcile_files


class ReconcileTests(unittest.TestCase):
    def test_flags_inactive_and_unmatched_accounts_without_recommending_revocation(self) -> None:
        result = reconcile(
            [{"email": "a@example.test", "name": "A", "status": "active"}],
            [
                {"email": " A@EXAMPLE.TEST ", "system": "Wiki", "account_type": "person"},
                {"email": "b@example.test", "system": "CRM", "account_type": "person"},
            ],
        )
        self.assertEqual(result["review_required"], 1)
        self.assertEqual(result["findings"][0]["finding"], "orphan_account")
        self.assertEqual(result["findings"][0]["decision"], "human_review_required")

    def test_flags_duplicate_and_ambiguous_identities(self) -> None:
        result = reconcile(
            [
                {"email": "a@example.test", "status": "active"},
                {"email": " A@EXAMPLE.TEST ", "status": "active"},
            ],
            [
                {"email": "a@example.test", "system": "Wiki"},
                {"email": "a@example.test", "system": "CRM"},
            ],
        )
        self.assertEqual([item["finding"] for item in result["findings"]], ["duplicate_account_identity"] * 2)

        ambiguous = reconcile(
            [
                {"email": "a@example.test", "status": "active"},
                {"email": " A@EXAMPLE.TEST ", "status": "active"},
            ],
            [{"email": "a@example.test", "system": "Wiki"}],
        )
        self.assertEqual(ambiguous["findings"][0]["finding"], "ambiguous_person_match")

    def test_missing_email_and_required_csv_columns_are_visible(self) -> None:
        result = reconcile([{"email": "a@example.test", "status": "active"}], [{"email": "", "system": "Wiki"}])
        self.assertEqual(result["findings"][0]["finding"], "missing_account_email")
        with tempfile.TemporaryDirectory() as temporary:
            incomplete = Path(temporary) / "incomplete.csv"
            incomplete.write_text("email,name\na@example.test,A\n", encoding="utf-8")
            accounts = Path(temporary) / "accounts.csv"
            accounts.write_text("email,system,account_type\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing columns: status"):
                reconcile_files(incomplete, accounts)

    def test_exception_requires_reason_and_must_match_an_account(self) -> None:
        result = reconcile(
            [],
            [{"email": "service@example.test", "system": "CI"}],
            [{"email": "service@example.test", "reason": "scheduled build identity"}],
        )
        self.assertEqual(result["exceptions_documented"], 1)
        self.assertEqual(result["review_required"], 0)

        invalid = reconcile(
            [],
            [{"email": "service@example.test", "system": "CI"}],
            [{"email": "service@example.test", "reason": " "}, {"email": "stale@example.test", "reason": "old account"}],
        )
        self.assertEqual({item["finding"] for item in invalid["findings"]}, {"orphan_account", "invalid_exception", "stale_exception"})


if __name__ == "__main__":
    unittest.main()
