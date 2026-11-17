"""Offline accountability tests."""
import unittest
from scripts.accountability import score


def sample(**changes):
    record = {
        "id": "a", "scoring_version": "forward_v2", "origin_utc": "2026-11-13T14:30:00+00:00",
        "entry_bar_utc": "2026-11-13T14:35:00+00:00",
        "recorded_utc": "2026-11-13T14:30:30+00:00",
        "target_utc": "2026-11-13T14:50:00+00:00",
        "prediction": {"direction": "UP", "up_probability_raw_shrunk": 0.7},
        "outcome": {"actual_return": 0.01, "evaluated_utc": "2026-11-13T14:55:00+00:00"},
    }
    record.update(changes)
    return record


class AccountabilityTests(unittest.TestCase):
    def test_forward_score(self):
        result = score([sample()])
        self.assertEqual(result["eligible_forecasts"], 1)
        self.assertEqual(result["directional_accuracy"], 1)
        self.assertEqual(result["brier_score"], 0.09)

    def test_missing_recorded_time_is_not_forward_evidence(self):
        result = score([sample(recorded_utc=None)])
        self.assertEqual(result["eligible_forecasts"], 0)
        self.assertEqual(result["excluded"]["no_verifiable_recording_time"], 1)

    def test_late_recording_is_excluded(self):
        result = score([sample(recorded_utc="2026-11-13T14:46:00+00:00")])
        self.assertEqual(result["excluded"]["not_proven_forward"], 1)

    def test_duplicates_are_excluded(self):
        result = score([sample(), sample()])
        self.assertEqual(result["eligible_forecasts"], 1)
        self.assertEqual(result["excluded"]["missing_or_duplicate_id"], 1)

    def test_unresolved_is_excluded(self):
        result = score([sample(target_utc=None, outcome=None)])
        self.assertEqual(result["excluded"]["unresolved"], 1)

    def test_uncertain_not_counted_as_directional(self):
        record = sample(prediction={"direction": "UNCERTAIN", "up_probability_raw_shrunk": 0.5})
        result = score([record])
        self.assertEqual(result["eligible_forecasts"], 1)
        self.assertEqual(result["directional_predictions"], 0)


if __name__ == "__main__":
    unittest.main()
