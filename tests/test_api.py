"""
API Tests for Mergington High School Activities Management System
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activity structure contains all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_includes_participants(self, client):
        """Test that participant lists are included"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "test@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup is prevented"""
        # First signup
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Second signup (duplicate)
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"

    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with URL-encoded activity name"""
        # Add an activity with special characters for testing
        activities["Art & Crafts"] = {
            "description": "Creative arts",
            "schedule": "Mondays",
            "max_participants": 10,
            "participants": []
        }
        
        response = client.post(
            "/activities/Art & Crafts/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess Club/signup?email=first.last+tag@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_participant_not_registered(self, client):
        """Test unregister for a participant who is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student not registered for this activity"

    def test_unregister_last_participant(self, client):
        """Test unregistering the last participant from an activity"""
        # Create activity with one participant
        activities["Solo Club"] = {
            "description": "Solo activities",
            "schedule": "Anytime",
            "max_participants": 5,
            "participants": ["solo@mergington.edu"]
        }
        
        response = client.delete(
            "/activities/Solo Club/unregister?email=solo@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant list is empty
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert len(data["Solo Club"]["participants"]) == 0


class TestIntegrationWorkflows:
    """Integration tests for complete workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities")
        assert email in after_signup.json()[activity]["participants"]
        assert len(after_signup.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        after_unregister = client.get("/activities")
        assert email not in after_unregister.json()[activity]["participants"]
        assert len(after_unregister.json()[activity]["participants"]) == initial_count

    def test_multiple_activities_signup(self, client):
        """Test signing up for multiple activities"""
        email = "multi@mergington.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Chess Club/signup?email={email}")
        client.post(f"/activities/Programming Class/signup?email={email}")
        client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Verify participant is in all activities
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]
        assert email in data["Gym Class"]["participants"]
