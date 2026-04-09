"""Tag API 集成测试（带鉴权 + project_id）"""


def test_create_tag(auth_client):
    client, project, headers = auth_client
    resp = client.post(
        "/api/v1/tags",
        json={"name": "bug", "color": "#FF0000", "project_id": project.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "bug"
    assert data["color"] == "#FF0000"


def test_list_tags(auth_client):
    client, project, headers = auth_client
    client.post(
        "/api/v1/tags",
        json={"name": "tag1", "project_id": project.id},
        headers=headers,
    )
    resp = client.get(f"/api/v1/tags?project_id={project.id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["tags"]) == 1


def test_get_tag(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tags",
        json={"name": "tag1", "project_id": project.id},
        headers=headers,
    )
    tag_id = cr.json()["id"]
    resp = client.get(f"/api/v1/tags/{tag_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "tag1"


def test_delete_tag(auth_client):
    client, project, headers = auth_client
    cr = client.post(
        "/api/v1/tags",
        json={"name": "del-me", "project_id": project.id},
        headers=headers,
    )
    tag_id = cr.json()["id"]
    resp = client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/api/v1/tags/{tag_id}", headers=headers).status_code == 404


def test_add_tags_to_ticket(auth_client):
    client, project, headers = auth_client
    tr = client.post(
        "/api/v1/tickets",
        json={"title": "T", "project_id": project.id},
        headers=headers,
    )
    tid = tr.json()["id"]

    t1 = client.post(
        "/api/v1/tags", json={"name": "a", "project_id": project.id}, headers=headers
    ).json()["id"]
    t2 = client.post(
        "/api/v1/tags", json={"name": "b", "project_id": project.id}, headers=headers
    ).json()["id"]

    resp = client.post(f"/api/v1/tickets/{tid}/tags", json=[t1, t2], headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["tags"]) == 2


def test_remove_tag_from_ticket(auth_client):
    client, project, headers = auth_client
    tr = client.post(
        "/api/v1/tickets",
        json={"title": "T", "project_id": project.id},
        headers=headers,
    )
    tid = tr.json()["id"]
    tag_id = client.post(
        "/api/v1/tags", json={"name": "x", "project_id": project.id}, headers=headers
    ).json()["id"]
    client.post(f"/api/v1/tickets/{tid}/tags", json=[tag_id], headers=headers)

    resp = client.delete(f"/api/v1/tickets/{tid}/tags/{tag_id}", headers=headers)
    assert resp.status_code == 204
    assert len(client.get(f"/api/v1/tickets/{tid}", headers=headers).json()["tags"]) == 0
