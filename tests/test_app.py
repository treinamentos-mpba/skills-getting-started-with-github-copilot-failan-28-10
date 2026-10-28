from copy import deepcopy

import pytest


def test_root_redirects_to_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client, activities):
    email = "newstudent@mergington.edu"
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].append(email)

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert client.get("/activities").json() == expected


def test_signup_rejects_duplicate(client, activities):
    email = activities["Chess Club"]["participants"][0]
    original = deepcopy(activities)

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == original


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_unknown_activity_is_rejected(client, activities, method):
    original = deepcopy(activities)

    response = client.request(
        method,
        "/activities/Unknown Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == original


def test_signup_rejects_full_activity(client, activities):
    activity = activities["Chess Club"]
    activity["max_participants"] = len(activity["participants"])
    original = deepcopy(activities)

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert client.get("/activities").json() == original


def test_remove_participant(client, activities):
    email = activities["Chess Club"]["participants"][0]
    expected = deepcopy(activities)
    expected["Chess Club"]["participants"].remove(email)

    response = client.delete("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert client.get("/activities").json() == expected


def test_remove_rejects_unregistered_participant(client, activities):
    original = deepcopy(activities)

    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "unregistered@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json() == original


@pytest.mark.parametrize("method", ["POST", "DELETE"])
def test_email_is_required(client, activities, method):
    original = deepcopy(activities)

    response = client.request(method, "/activities/Chess Club/signup")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == original


def test_signup_then_remove_restores_activity(client, activities):
    original = deepcopy(activities)
    email = "newstudent@mergington.edu"
    endpoint = "/activities/Chess Club/signup"

    signup_response = client.post(endpoint, params={"email": email})

    assert signup_response.status_code == 200
    assert email in client.get("/activities").json()["Chess Club"]["participants"]

    removal_response = client.delete(endpoint, params={"email": email})

    assert removal_response.status_code == 200
    assert client.get("/activities").json() == original