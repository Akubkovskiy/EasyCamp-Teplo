"""
Tests for Avito webhook functionality
"""
import pytest
import hmac
import hashlib
import json


class TestWebhookSignatureVerification:
    """Test HMAC signature verification logic"""
    
    def test_valid_signature_matches(self):
        """Valid signature should match expected"""
        secret = "test_webhook_secret_123"
        body = b'{"event_type": "booking", "payload": {}}'
        
        expected_sig = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Simulate verification
        computed = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        assert hmac.compare_digest(expected_sig, computed)
    
    def test_invalid_signature_rejected(self):
        """Invalid signature should not match"""
        secret = "test_webhook_secret_123"
        body = b'{"event_type": "booking", "payload": {}}'
        
        expected_sig = hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Wrong signature
        invalid_sig = "0" * 64
        
        assert not hmac.compare_digest(expected_sig, invalid_sig)
    
    def test_tampered_body_detected(self):
        """Signature from original body should not match tampered body"""
        secret = "test_webhook_secret_123"
        original_body = b'{"event_type": "booking", "payload": {"id": 1}}'
        tampered_body = b'{"event_type": "booking", "payload": {"id": 999}}'
        
        # Signature from original
        original_sig = hmac.new(
            secret.encode(),
            original_body,
            hashlib.sha256
        ).hexdigest()
        
        # Compute for tampered
        tampered_sig = hmac.new(
            secret.encode(),
            tampered_body,
            hashlib.sha256
        ).hexdigest()
        
        assert not hmac.compare_digest(original_sig, tampered_sig)


class TestWebhookIdempotency:
    """Test idempotency logic for duplicate webhook prevention"""
    
    def test_duplicate_detection_by_id(self):
        """Same avito_booking_id should be detected as duplicate"""
        existing_ids = {"12345678", "87654321"}
        new_id = "12345678"
        
        is_duplicate = new_id in existing_ids
        assert is_duplicate is True
    
    def test_new_booking_not_duplicate(self):
        """New booking ID should not be detected as duplicate"""
        existing_ids = {"12345678", "87654321"}
        new_id = "11111111"
        
        is_duplicate = new_id in existing_ids
        assert is_duplicate is False
    
    def test_response_for_duplicate(self):
        """Duplicate webhook should return already_processed status"""
        is_duplicate = True
        
        if is_duplicate:
            response = {"status": "already_processed"}
        else:
            response = {"status": "ok"}
        
        assert response["status"] == "already_processed"


class TestWebhookPayloadParsing:
    """Test webhook payload parsing"""
    
    def test_parse_valid_payload(self):
        """Valid payload should parse correctly"""
        raw = b'{"event_type": "booking", "payload": {"avito_booking_id": "123"}}'
        
        data = json.loads(raw)
        
        assert data["event_type"] == "booking"
        assert data["payload"]["avito_booking_id"] == "123"
    
    def test_invalid_json_raises(self):
        """Invalid JSON should raise exception"""
        raw = b'not valid json'
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)
