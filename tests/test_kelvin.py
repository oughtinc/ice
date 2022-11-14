from fastapi.testclient import TestClient

from ice.kelvin.workspace import Workspace
from ice.routes.kelvin import router

client = TestClient(router)


def test_hello_world():
    response = client.get("/kelvin/hello/")
    assert response.status_code == 200
    assert response.json() == "Hello World"


def test_initial_workspace():
    response = client.get("/kelvin/workspaces/initial")
    assert response.status_code == 200
    workspace = Workspace(**response.json())
    assert workspace.frontier().focus_path().label == "Main"


def test_execute_actions():
    ws_response = client.get("/kelvin/workspaces/initial")
    workspace = Workspace(**ws_response.json())
    frontier = workspace.frontier()
    actions_response = client.post("/kelvin/actions/available", json=frontier.dict())
    assert actions_response.status_code == 200
    actions = actions_response.json()
    assert len(actions) > 0
    for action in actions:
        print(action)
        params = action["params"]
        for param in params:
            if param["value"] is None:
                param["value"] = "test"
        action_response = client.post(
            "/kelvin/actions/execute",
            json={"action": action, "frontier": frontier.dict()},
        )
        assert action_response.status_code == 200
