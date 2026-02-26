"""
Tests for risk classification logic in conversational_ops_service.
"""

import pytest
from app.services.conversational_ops_service import _classify_risk


class TestDeleteAlwaysHigh:
    def test_delete_one_record(self):
        assert _classify_risk("DELETE", "student", 1) == "HIGH"

    def test_delete_zero_records(self):
        assert _classify_risk("DELETE", "student", 0) == "HIGH"

    def test_delete_hundred_records(self):
        assert _classify_risk("DELETE", "student", 100) == "HIGH"

    def test_delete_course(self):
        assert _classify_risk("DELETE", "course", 5) == "HIGH"


class TestUserModificationAlwaysHigh:
    def test_update_user(self):
        assert _classify_risk("UPDATE", "user", 1) == "HIGH"

    def test_create_user(self):
        assert _classify_risk("CREATE", "user", 1) == "HIGH"

    def test_read_user_not_high(self):
        assert _classify_risk("READ", "user", 1) == "LOW"


class TestBulkOperationHigh:
    def test_update_sixty_records(self):
        assert _classify_risk("UPDATE", "student", 60) == "HIGH"

    def test_create_fifty_one_records(self):
        assert _classify_risk("CREATE", "course", 51) == "HIGH"

    def test_update_fifty_records_not_high(self):
        # Exactly at threshold is not HIGH, it is MEDIUM
        assert _classify_risk("UPDATE", "student", 50) == "MEDIUM"


class TestWriteOperationMedium:
    def test_update_five_records(self):
        assert _classify_risk("UPDATE", "student", 5) == "MEDIUM"

    def test_create_one_record(self):
        assert _classify_risk("CREATE", "course", 1) == "MEDIUM"

    def test_update_ten_records(self):
        assert _classify_risk("UPDATE", "student", 10) == "MEDIUM"


class TestReadAlwaysLow:
    def test_read_one_record(self):
        assert _classify_risk("READ", "student", 1) == "LOW"

    def test_read_nine_records(self):
        assert _classify_risk("READ", "student", 9) == "LOW"

    def test_analyze_any_count(self):
        assert _classify_risk("ANALYZE", "student", 100) == "LOW"

    def test_read_zero_records(self):
        assert _classify_risk("READ", "student", 0) == "LOW"
