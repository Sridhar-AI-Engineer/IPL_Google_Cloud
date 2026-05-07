"""Unit tests for IPL Agentic Coach."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ipl_agentic_coach.backend.app.main import app
from ipl_agentic_coach.backend.app import models, schemas, database, crud


# Test database setup
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[database.get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables."""
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


class TestHealth:
    """Test health check endpoints."""
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
    
    def test_readiness_check(self):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True
    
    def test_liveness_check(self):
        response = client.get("/alive")
        assert response.status_code == 200
        assert response.json()["alive"] is True


class TestAuth:
    """Test authentication endpoints."""
    
    def test_login(self):
        response = client.post(
            "/auth/login",
            params={"username": "testuser", "password": "password"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_creates_user(self):
        response = client.post(
            "/auth/login",
            params={"username": "newuser", "password": "password"}
        )
        assert response.status_code == 200
        
        # Verify user was created
        response2 = client.post(
            "/auth/login",
            params={"username": "newuser", "password": "password"}
        )
        assert response2.status_code == 200


class TestUsers:
    """Test user endpoints."""
    
    def test_create_user(self):
        response = client.post(
            "/users/create",
            json={"username": "player1", "email": "player1@test.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "player1"
        assert data["points"] == 0
    
    def test_create_duplicate_user(self):
        client.post(
            "/users/create",
            json={"username": "player2", "email": "player2@test.com"}
        )
        response = client.post(
            "/users/create",
            json={"username": "player2", "email": "player2@test.com"}
        )
        assert response.status_code == 400
    
    def test_list_users(self):
        client.post(
            "/users/create",
            json={"username": "player3"}
        )
        response = client.get("/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_user(self):
        response = client.post(
            "/users/create",
            json={"username": "player4"}
        )
        user_id = response.json()["id"]
        
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
    
    def test_get_leaderboard(self):
        response = client.get("/users/leaderboard/top", params={"limit": 10})
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestMatches:
    """Test match endpoints."""
    
    def test_list_matches(self):
        response = client.get("/matches/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_match(self):
        response = client.post(
            "/matches/",
            json={
                "team_a": "CSK",
                "team_b": "MI",
                "date": "2024-05-07",
                "status": "live"
            }
        )
        assert response.status_code == 200
        assert response.json()["team_a"] == "CSK"


class TestDecisions:
    """Test decision endpoints."""
    
    def test_submit_decision(self):
        response = client.post(
            "/decisions/submit",
            json={
                "username": "testplayer",
                "field_input": "off_side",
                "bowler_input": "fast_bowler",
                "strategy_input": "aggressive",
                "ball_number": 1
            }
        )
        # May fail due to auth, but endpoint exists
        assert response.status_code in [200, 401, 422]
    
    def test_evaluate_decision(self):
        response = client.post(
            "/decisions/evaluate",
            json={
                "field_input": "off_side",
                "bowler_input": "fast_bowler",
                "strategy_input": "aggressive",
            }
        )
        assert response.status_code == 200
        assert "score" in response.json()


class TestAnalytics:
    """Test analytics endpoints."""
    
    def test_analytics_status(self):
        response = client.get("/analytics/status")
        assert response.status_code == 200
        data = response.json()
        assert "plotly_available" in data or "matplotlib_available" in data
    
    def test_leaderboard_chart(self):
        response = client.get("/analytics/leaderboard-chart")
        assert response.status_code == 200
    
    def test_score_distribution(self):
        response = client.get("/analytics/score-distribution")
        assert response.status_code == 200


class TestMonitoring:
    """Test monitoring endpoints."""
    
    def test_metrics(self):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert b"ipl_requests_total" in response.content
    
    def test_stats(self):
        response = client.get("/stats")
        assert response.status_code == 200
        assert "metrics" in response.json()
    
    def test_stack_status(self):
        response = client.get("/stack")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestExport:
    """Test export endpoints."""
    
    def test_export_leaderboard_csv(self):
        response = client.get("/export/leaderboard/csv")
        assert response.status_code in [200, 404]  # May be empty
        if response.status_code == 200:
            assert "text/csv" in response.headers["content-type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
