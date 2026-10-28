from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activities):
    with TestClient(app_module.app) as test_client:
        yield test_client