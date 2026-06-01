"""Tests for authentication and password hashing."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPasswordHashing:
    """Tests for utils.hash_password and verify_password."""

    def test_hash_password_deterministic(self):
        from app.services.utils import hash_password
        h1 = hash_password("test123")
        h2 = hash_password("test123")
        assert h1 == h2

    def test_hash_password_different_inputs(self):
        from app.services.utils import hash_password
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_hash_password_returns_hex_string(self):
        from app.services.utils import hash_password
        h = hash_password("test")
        assert len(h) == 64  # SHA-256 hex digest length
        assert all(c in "0123456789abcdef" for c in h)

    def test_verify_password_correct(self):
        from app.services.utils import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        from app.services.utils import hash_password, verify_password
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        from app.services.utils import hash_password, verify_password
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestAuthLogin:
    """Tests for POST /api/auth/login endpoint."""

    def test_login_with_default_teacher(self):
        response = client.post(
            "/api/auth/login",
            json={"teacher_id": "T001", "password": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["teacher"]["id"] == "T001"
        assert data["token"].startswith("dev-token-")
        assert isinstance(data["classes"], list)

    def test_login_with_wrong_password(self):
        response = client.post(
            "/api/auth/login",
            json={"teacher_id": "T001", "password": "wrong"},
        )
        assert response.status_code == 401
        assert "密码错误" in response.json()["detail"]

    def test_login_with_nonexistent_teacher(self):
        response = client.post(
            "/api/auth/login",
            json={"teacher_id": "NONEXISTENT", "password": "dev"},
        )
        assert response.status_code == 401
        assert "教师不存在" in response.json()["detail"]

    def test_login_with_phone(self):
        response = client.post(
            "/api/auth/login",
            json={"phone": "13800000001", "password": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["teacher"]["id"] == "T001"

    def test_login_returns_classes(self):
        response = client.post(
            "/api/auth/login",
            json={"teacher_id": "T001", "password": "dev"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["classes"], list)


class TestAuthMe:
    """Tests for GET /api/auth/me endpoint."""

    def test_get_current_teacher_default(self):
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "T001"
        assert data["name"] == "王老师"

    def test_get_current_teacher_by_id(self):
        response = client.get("/api/auth/me?teacher_id=T001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "T001"

    def test_get_nonexistent_teacher(self):
        response = client.get("/api/auth/me?teacher_id=NONEXISTENT")
        assert response.status_code == 404
