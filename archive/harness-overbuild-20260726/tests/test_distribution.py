from __future__ import annotations

import unittest

from harness.distribution import DistributionPlanError, validate_distribution_plan


def valid_distribution_plan() -> dict:
    return {
        "primary_reader": {
            "role": "reader-role",
            "context": "reader-context",
            "job": "reader-job",
            "pain": "reader-pain",
            "desired_outcome": "reader-outcome",
            "awareness": "reader-awareness",
            "objection": "",
        },
        "reader_action": "reader-action",
        "content_atoms": [
            {
                "id": "atom-1",
                "type": "claim",
                "content": "content",
                "source_boundary": "confirmed-source",
            }
        ],
        "portfolio": [
            {
                "id": "post-1",
                "platform": "example-platform",
                "format": "short-post",
                "job": "explain",
                "angle": "primary-angle",
                "atom_ids": ["atom-1"],
                "hook_strategy": "lead-with-reader-value",
                "value_delivery": "explain-the-claim",
                "engagement": "invite-relevant-experience",
                "cta": {
                    "mode": "none",
                    "promise": "",
                    "destination_status": "not_needed",
                    "destination": "",
                },
            }
        ],
        "platform_checks": [
            {
                "platform": "example-platform",
                "status": "not_required",
                "checked_at": "",
                "sources": [],
                "constraints": [],
            }
        ],
        "trend": {
            "status": "not_requested",
            "bridge": "",
            "sources": [],
        },
    }


class DistributionPlanTests(unittest.TestCase):
    def test_valid_plan_returns_normalized_structure(self) -> None:
        plan = validate_distribution_plan(valid_distribution_plan())

        self.assertEqual(plan["content_atoms"][0]["id"], "atom-1")
        self.assertEqual(plan["portfolio"][0]["atom_ids"], ["atom-1"])
        self.assertEqual(plan["trend"]["status"], "not_requested")

    def test_unknown_atom_reference_is_rejected(self) -> None:
        plan = valid_distribution_plan()
        plan["portfolio"][0]["atom_ids"] = ["missing-atom"]

        with self.assertRaises(DistributionPlanError):
            validate_distribution_plan(plan)

    def test_enabled_cta_requires_destination_when_marked_provided(self) -> None:
        plan = valid_distribution_plan()
        plan["portfolio"][0]["cta"] = {
            "mode": "first_comment_or_reply",
            "promise": "resource",
            "destination_status": "provided",
            "destination": "",
        }

        with self.assertRaises(DistributionPlanError):
            validate_distribution_plan(plan)

    def test_verified_platform_check_requires_evidence(self) -> None:
        plan = valid_distribution_plan()
        plan["platform_checks"][0]["status"] = "verified"

        with self.assertRaises(DistributionPlanError):
            validate_distribution_plan(plan)


if __name__ == "__main__":
    unittest.main()
