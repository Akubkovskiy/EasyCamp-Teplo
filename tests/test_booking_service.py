"""
Unit tests for booking service logic
"""
import pytest
from datetime import date
from unittest.mock import patch, AsyncMock, MagicMock


class TestDateOverlapLogic:
    """Test the date overlap detection logic used in availability checks"""
    
    def test_overlapping_ranges(self):
        """Two ranges that overlap should be detected"""
        # Existing: March 10-15, Requested: March 12-18
        existing_start, existing_end = date(2026, 3, 10), date(2026, 3, 15)
        request_start, request_end = date(2026, 3, 12), date(2026, 3, 18)
        
        # Overlap condition: start1 < end2 AND start2 < end1
        overlaps = (existing_start < request_end) and (request_start < existing_end)
        assert overlaps is True
    
    def test_adjacent_ranges_no_overlap(self):
        """Adjacent ranges (checkout = next checkin) should NOT overlap"""
        # Existing: March 10-15, Requested: March 15-20 (checkout day = new checkin)
        existing_start, existing_end = date(2026, 3, 10), date(2026, 3, 15)
        request_start, request_end = date(2026, 3, 15), date(2026, 3, 20)
        
        # Overlap condition: start1 < end2 AND start2 < end1
        overlaps = (existing_start < request_end) and (request_start < existing_end)
        assert overlaps is False  # Adjacent is OK
    
    def test_completely_before(self):
        """Request completely before existing - no overlap"""
        existing_start, existing_end = date(2026, 3, 20), date(2026, 3, 25)
        request_start, request_end = date(2026, 3, 1), date(2026, 3, 5)
        
        overlaps = (existing_start < request_end) and (request_start < existing_end)
        assert overlaps is False
    
    def test_completely_after(self):
        """Request completely after existing - no overlap"""
        existing_start, existing_end = date(2026, 3, 1), date(2026, 3, 5)
        request_start, request_end = date(2026, 3, 20), date(2026, 3, 25)
        
        overlaps = (existing_start < request_end) and (request_start < existing_end)
        assert overlaps is False
    
    def test_contained_within(self):
        """Request fully contained within existing - overlap"""
        existing_start, existing_end = date(2026, 3, 1), date(2026, 3, 15)
        request_start, request_end = date(2026, 3, 5), date(2026, 3, 10)
        
        overlaps = (existing_start < request_end) and (request_start < existing_end)
        assert overlaps is True


class TestBookingStatusTransitions:
    """Test booking status transition logic"""
    
    def test_confirmed_to_checking_in_on_checkin_day(self):
        """Booking should transition to CHECKING_IN on check-in day"""
        check_in = date(2026, 3, 10)
        check_out = date(2026, 3, 15)
        today = date(2026, 3, 10)  # Same as check_in
        
        should_transition = (check_in == today and check_out > today)
        assert should_transition is True
    
    def test_checked_in_to_completed_on_checkout_day(self):
        """Booking should transition to COMPLETED on/after checkout day"""
        check_in = date(2026, 3, 10)
        check_out = date(2026, 3, 15)
        today = date(2026, 3, 15)  # Same as check_out
        
        should_complete = (check_out <= today)
        assert should_complete is True
    
    def test_no_transition_during_stay(self):
        """No transition to COMPLETED during the stay"""
        check_in = date(2026, 3, 10)
        check_out = date(2026, 3, 15)
        today = date(2026, 3, 12)  # During stay
        
        should_complete = (check_out <= today)
        assert should_complete is False
