import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from src.app import app


@pytest.fixture
def client():
    """Fixture that provides a TestClient for the FastAPI app"""
    return TestClient(app)


class TestActivitiesAPI:
    """Test suite for the activities API endpoints"""

    def test_get_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        
        # Check we have the expected number of activities
        assert len(activities) == 9
        
        # Check structure of first activity
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_has_initial_participants(self, client):
        """Test that activities have their initial participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check Chess Club has initial participants
        chess_participants = activities["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        email = "test@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert f"Signed up {email} for {activity}" in result["message"]
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_duplicate_participant(self, client):
        """Test signing up the same participant twice"""
        email = "duplicate@mergington.edu"
        activity = "Programming Class"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "Student already signed up" in result["detail"]

    def test_delete_participant_success(self, client):
        """Test successful deletion of a participant"""
        email = "to_delete@mergington.edu"
        activity = "Gym Class"
        
        # First add the participant
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Now delete them
        response = client.delete(f"/activities/{activity}/participants/{email}")
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert f"Unregistered {email} from {activity}" in result["message"]
        
        # Verify they were removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity]["participants"]

    def test_delete_participant_activity_not_found(self, client):
        """Test deleting from non-existent activity"""
        response = client.delete("/activities/NonExistentActivity/participants/test@mergington.edu")
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_delete_participant_not_signed_up(self, client):
        """Test deleting a participant who isn't signed up"""
        response = client.delete("/activities/Chess Club/participants/not_signed_up@mergington.edu")
        assert response.status_code == 404
        result = response.json()
        assert "Student not signed up" in result["detail"]

    def test_root_redirect(self, client):
        """Test that GET / redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]