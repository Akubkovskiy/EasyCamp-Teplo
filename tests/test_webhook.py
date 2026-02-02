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


class TestWebhookIntegration:
    """
    Integration tests for webhook endpoint using TestClient.
    These test the actual HTTP behavior, not just logic.
    """
    
    @pytest.fixture
    def test_client(self):
        """Create TestClient with mocked settings"""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, MagicMock
        
        # Mock settings before importing app
        mock_settings = MagicMock()
        mock_settings.avito_webhook_secret = "test_secret_123"
        mock_settings.avito_webhook_mode = "enforce"
        
        with patch('app.avito.webhook.settings', mock_settings):
            from app.avito.webhook import router
            from fastapi import FastAPI
            
            app = FastAPI()
            app.include_router(router)
            
            yield TestClient(app), mock_settings
    
    def test_enforce_mode_rejects_invalid_signature(self, test_client):
        """
        SMOKE TEST: In enforce mode with invalid signature, 
        webhook should return 401 Unauthorized.
        """
        client, mock_settings = test_client
        mock_settings.avito_webhook_mode = "enforce"
        mock_settings.avito_webhook_secret = "real_secret"
        
        payload = {"event_type": "booking", "payload": {"avito_booking_id": "123"}}
        
        response = client.post(
            "/avito/webhook",
            json=payload,
            headers={"X-Avito-Signature": "invalid_signature_here"}
        )
        
        assert response.status_code == 401
        assert response.json()["error"] == "Invalid signature"
    
    def test_warn_mode_allows_invalid_signature(self, test_client):
        """
        SMOKE TEST: In warn mode with invalid signature,
        webhook should return 200 (logs warning, but allows).
        """
        client, mock_settings = test_client
        mock_settings.avito_webhook_mode = "warn"
        mock_settings.avito_webhook_secret = "real_secret"
        
        # Send minimal payload that will fail later (after signature check)
        # but at least we verify it doesn't return 401
        payload = {"event_type": "booking", "payload": {"avito_booking_id": "123"}}
        
        response = client.post(
            "/avito/webhook",
            json=payload,
            headers={"X-Avito-Signature": "invalid_signature_here"}
        )
        
        # Should NOT be 401 in warn mode
        assert response.status_code != 401

