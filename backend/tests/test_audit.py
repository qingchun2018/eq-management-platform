"""审计日志 API：组长可访问"""


def test_audit_logs_team_admin(auth_client):
    client, project, headers = auth_client
    resp = client.get("/api/v1/audit-logs", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_audit_logs_filter_by_project(auth_client):
    client, project, headers = auth_client
    resp = client.get(
        f"/api/v1/audit-logs?project_id={project.id}",
        headers=headers,
    )
    assert resp.status_code == 200


def test_audit_logs_unauthorized(client):
    r = client.get("/api/v1/audit-logs")
    assert r.status_code == 401
