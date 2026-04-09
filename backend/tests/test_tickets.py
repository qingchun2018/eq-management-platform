"""Ticket API 集成测试（带鉴权 + project_id）"""


def test_create_ticket(auth_client):
    client, project, headers = auth_client
    resp = client.post(
        "/api/v1/tickets",
        json={"title": "Test Ticket", "description": "Desc", "project_id": project.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Ticket"
    assert data["status"] == "pending"
    assert data["project_id"] == project.id


def test_list_tickets(auth_client):
    client, project, headers = auth_client
    client.post(
        "/api/v1/tickets",
        json={"title": "T1", "project_id": project.id},
        headers=headers,
    )
    resp = client.get(f"/api/v1/tickets?project_id={project.id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["tickets"]) == 1


def test_get_ticket(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tickets",
        json={"title": "T1", "project_id": project.id},
        headers=headers,
    )
    tid = cr.json()["id"]
    resp = client.get(f"/api/v1/tickets/{tid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "T1"


def test_update_ticket(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tickets",
        json={"title": "Old", "project_id": project.id},
        headers=headers,
    )
    tid = cr.json()["id"]
    resp = client.put(
        f"/api/v1/tickets/{tid}",
        json={"title": "New"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


def test_delete_ticket(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tickets",
        json={"title": "Del", "project_id": project.id},
        headers=headers,
    )
    tid = cr.json()["id"]
    resp = client.delete(f"/api/v1/tickets/{tid}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/api/v1/tickets/{tid}", headers=headers).status_code == 404


def test_complete_and_uncomplete(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tickets",
        json={"title": "Complete Me", "project_id": project.id},
        headers=headers,
    )
    tid = cr.json()["id"]
    resp = client.patch(f"/api/v1/tickets/{tid}/complete", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    resp2 = client.patch(f"/api/v1/tickets/{tid}/uncomplete", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "pending"


def test_filter_by_status(auth_client):
    client, project, headers = auth_client
    client.post("/api/v1/tickets", json={"title": "A", "project_id": project.id}, headers=headers)
    cr = client.post(
        "/api/v1/tickets", json={"title": "B", "project_id": project.id}, headers=headers
    )
    client.patch(f"/api/v1/tickets/{cr.json()['id']}/complete", headers=headers)

    resp = client.get(f"/api/v1/tickets?project_id={project.id}&status=pending", headers=headers)
    assert all(t["status"] == "pending" for t in resp.json()["tickets"])


def test_search_tickets(auth_client):
    client, project, headers = auth_client
    client.post(
        "/api/v1/tickets", json={"title": "Searchable", "project_id": project.id}, headers=headers
    )
    client.post(
        "/api/v1/tickets", json={"title": "Other", "project_id": project.id}, headers=headers
    )
    resp = client.get(
        f"/api/v1/tickets?project_id={project.id}&search=Search", headers=headers
    )
    assert len(resp.json()["tickets"]) == 1


def test_unauthenticated_returns_401(client, seeded):
    resp = client.get("/api/v1/tickets?project_id=1")
    assert resp.status_code == 401
