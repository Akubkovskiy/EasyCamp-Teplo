"""
Integration tests for Avito webhook endpoint using TestClient.
These test the actual HTTP behavior, not just logic.

Note: These tests mock settings before importing the router to ensure
the mock is applied. This is somewhat fragile but works for smoke tests.
"""
import pytest


@pytest.mark.integration
class TestWebhookIntegration:
    """Integration tests for webhook endpoint modes"""
    
    @pytest.fixture
    def test_client(self):
        """Create TestClient with mocked settings"""
        from fastapi.testclient import TestClient
        from unittest.mock import patch, MagicMock
        
        # Mock settings before importing router
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
        webhook should return 200 (logs warning, but allows request through).
        """
        client, mock_settings = test_client
        mock_settings.avito_webhook_mode = "warn"
        mock_settings.avito_webhook_secret = "real_secret"
        
        payload = {"event_type": "booking", "payload": {"avito_booking_id": "123"}}
        
        response = client.post(
            "/avito/webhook",
            json=payload,
            headers={"X-Avito-Signature": "invalid_signature_here"}
        )
        
        # This tests signature mode only, not full processing path.
        # Downstream 400/500 is acceptable — we're verifying warn mode
        # doesn't reject with 401 like enforce mode would.
        assert response.status_code != 401, f"Unexpected 401 in warn mode: {response.text}"
