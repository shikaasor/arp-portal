import pytest

from .conftest import apply, auth


@pytest.fixture
def app_id(client, repo):
    repo.add_user("alice")
    res = apply(client, repo)
    assert res.status_code == 201
    return res.json()["id"]


@pytest.fixture
def reviewers(repo):
    repo.add_user("national", role="national")
    repo.add_user("kano", role="state", state="Kano")
    repo.add_user("kaduna", role="state", state="Kaduna")
    repo.add_user("nassarawa", role="lga", state="Kano", lga="Nasarawa")
    repo.add_user("gama", role="ward", state="Kano", lga="Nasarawa", ward="Gama")
    repo.add_user("incomplete", role="lga", state="Kano")


def review(client, token, app_id, action="approve", note=None):
    return client.post(
        f"/api/admin/applications/{app_id}/review",
        headers=auth(token),
        json={"action": action, "note": note},
    )


def test_applicants_cannot_access_admin(client, app_id):
    assert client.get("/api/admin/applications", headers=auth("alice")).status_code == 403


def test_incomplete_assignment_denied(client, app_id, reviewers):
    assert client.get("/api/admin/applications", headers=auth("incomplete")).status_code == 403


def test_geographic_scoping(client, app_id, reviewers):
    def total(token, **params):
        res = client.get("/api/admin/applications", headers=auth(token), params=params)
        return res.json()["total"]

    assert total("national") == 1
    assert total("kano") == 1
    assert total("kaduna") == 0
    # A state reviewer cannot widen scope through the query string
    assert total("kaduna", state="Kano") == 0
    assert total("gama") == 1


def test_full_review_workflow(client, repo, app_id, reviewers):
    # LGA reviewer cannot act before the state stage is complete
    assert review(client, "nassarawa", app_id).status_code == 409
    assert review(client, "kaduna", app_id).status_code == 404

    assert review(client, "kano", app_id).json()["stage"] == "lga_review"
    assert review(client, "nassarawa", app_id).json()["stage"] == "ward_review"
    assert review(client, "gama", app_id).json()["stage"] == "approved"
    # Finished applications cannot be reviewed again
    assert review(client, "national", app_id).status_code == 409

    history = client.get("/api/me", headers=auth("alice")).json()["application"]["history"]
    assert [h["action"] for h in history] == ["submitted", "approve", "approve", "approve"]


def test_reject_requires_note(client, app_id, reviewers):
    assert review(client, "kano", app_id, action="reject").status_code == 422
    res = review(client, "kano", app_id, action="reject", note="Incomplete documents")
    assert res.json()["stage"] == "rejected"
    me = client.get("/api/me", headers=auth("alice")).json()
    assert me["application"]["feedback"] == "Incomplete documents"


def test_national_can_act_at_any_active_stage(client, app_id, reviewers):
    assert review(client, "national", app_id).json()["stage"] == "lga_review"


def test_kyc_national_only_and_audited(client, repo, app_id, reviewers):
    for token in ("alice", "kano", "gama"):
        assert (
            client.get(f"/api/admin/applications/{app_id}/kyc", headers=auth(token)).status_code
            == 403
        )
    res = client.get(f"/api/admin/applications/{app_id}/kyc", headers=auth("national"))
    assert res.status_code == 200
    body = res.json()
    assert body["identification_number"] == "12345678901"
    assert body["identity_document_url"].startswith("https://signed.example/")
    assert any(e["action"] == "kyc_viewed" for e in repo.events)
    # The audit event is not shown to the applicant
    history = client.get("/api/me", headers=auth("alice")).json()["application"]["history"]
    assert all(h["action"] != "kyc_viewed" for h in history)
