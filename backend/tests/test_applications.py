import json

from .conftest import JPEG, PDF, PNG, apply, auth, declared, valid_details


def test_requires_authentication(client):
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", headers=auth("nobody")).status_code == 401
    assert client.post("/api/applications/uploads", json=declared()).status_code == 401


def test_me_without_application(client, repo):
    repo.add_user("alice")
    body = client.get("/api/me", headers=auth("alice")).json()
    assert body["profile"]["role"] == "applicant"
    assert body["application"] is None


def test_upload_tickets_are_scoped_to_user_and_reference(client, repo):
    uid = repo.add_user("alice")
    body = client.post("/api/applications/uploads", headers=auth("alice"), json=declared()).json()
    assert body["bucket"] == "applicant-documents"
    ref = body["reference"]
    assert body["uploads"]["identity_document"]["path"] == f"{uid}/{ref}/identity_document.pdf"
    assert body["uploads"]["passport_photograph"]["path"] == f"{uid}/{ref}/passport_photograph.jpg"
    assert body["uploads"]["identity_document"]["token"]


def test_submit_and_track(client, repo):
    repo.add_user("alice")
    res = apply(client, repo)
    assert res.status_code == 201, res.text
    ref = res.json()["reference"]
    assert ref.startswith("ARP-")

    me = client.get("/api/me", headers=auth("alice")).json()
    assert me["application"]["reference"] == ref
    assert me["application"]["stage"] == "state_review"
    assert me["application"]["history"][0]["action"] == "submitted"
    # KYC never appears in applicant views
    assert "identification_number" not in json.dumps(me)
    app_id = me["application"]["id"]
    assert repo.kyc[app_id]["identification_number"] == "12345678901"
    assert repo.kyc[app_id]["identity_document_path"].endswith(".pdf")
    assert "identification_number" not in repo.applications[app_id]


def test_one_application_per_user(client, repo):
    repo.add_user("alice")
    assert apply(client, repo).status_code == 201
    assert (
        client.post("/api/applications/uploads", headers=auth("alice"), json=declared()).status_code
        == 409
    )
    assert apply(client, repo).status_code == 409


def test_email_verification_required(client, repo):
    repo.add_user("alice", verified=False)
    assert apply(client, repo).status_code == 403


def test_validation_errors_are_readable(client, repo):
    repo.add_user("alice")
    cases = [
        valid_details(identification_number="123"),
        valid_details(
            identification_type="International Passport", identification_number="12345678901"
        ),
        valid_details(business_idea="too short"),
        valid_details(state="Lagos"),
        valid_details(date_of_birth="2020-01-01"),
        valid_details(phone="call me"),
        valid_details(unexpected="field"),
    ]
    for details in cases:
        res = apply(client, repo, details=details)
        assert res.status_code == 422, (details, res.text)
        assert isinstance(res.json()["detail"], str)
    assert repo.applications == {}


def test_passport_number_normalised(client, repo):
    repo.add_user("alice")
    res = apply(
        client,
        repo,
        details=valid_details(
            identification_type="International Passport", identification_number="a 12345678"
        ),
    )
    assert res.status_code == 201
    assert next(iter(repo.kyc.values()))["identification_number"] == "A12345678"


def test_rejects_declared_types_and_sizes(client, repo, settings):
    repo.add_user("alice")
    bad = [
        declared(identity_type="text/html"),
        declared(photo_type="application/pdf"),  # PDF not allowed for the photograph
        declared(size=0),
    ]
    for body in bad:
        assert client.post(
            "/api/applications/uploads", headers=auth("alice"), json=body
        ).status_code in (413, 415, 422)
    settings.max_upload_bytes = 100
    assert (
        client.post(
            "/api/applications/uploads", headers=auth("alice"), json=declared(size=101)
        ).status_code
        == 413
    )


def test_rejects_stored_files_that_lie_about_their_type(client, repo):
    repo.add_user("alice")
    # Declared PDF, but the bytes uploaded are not a PDF
    assert apply(client, repo, identity=b"<script>").status_code == 415
    # Declared JPEG, but a PNG was uploaded
    assert apply(client, repo, photo=PNG).status_code == 415
    assert repo.files == {}  # bad uploads are cleaned up
    assert apply(client, repo, photo=PNG, photo_type="image/png").status_code == 201


def test_rejects_oversized_stored_files(client, repo, settings):
    repo.add_user("alice")
    settings.max_upload_bytes = 100
    res = apply(client, repo, identity=b"%PDF-" + b"0" * 200, photo=JPEG[:50])
    assert res.status_code == 413


def test_missing_upload(client, repo):
    repo.add_user("alice")
    start = client.post("/api/applications/uploads", headers=auth("alice"), json=declared()).json()
    res = client.post(
        "/api/applications",
        headers=auth("alice"),
        json={
            "reference": start["reference"],
            "details": valid_details(),
            "identity_document_path": start["uploads"]["identity_document"]["path"],
            "passport_photograph_path": start["uploads"]["passport_photograph"]["path"],
        },
    )
    assert res.status_code == 422
    assert "not uploaded" in res.json()["detail"]


def test_cannot_claim_another_users_files(client, repo):
    repo.add_user("alice")
    bob = repo.add_user("bob")
    start = client.post("/api/applications/uploads", headers=auth("bob"), json=declared()).json()
    for key in ("identity_document", "passport_photograph"):
        repo.browser_upload(
            start["uploads"][key]["path"], PDF if key == "identity_document" else JPEG
        )
    stolen = {
        "reference": start["reference"],
        "details": valid_details(),
        "identity_document_path": start["uploads"]["identity_document"]["path"],
        "passport_photograph_path": start["uploads"]["passport_photograph"]["path"],
    }
    assert bob in stolen["identity_document_path"]
    res = client.post("/api/applications", headers=auth("alice"), json=stolen)
    assert res.status_code == 422
    # Path traversal / foreign prefixes are rejected too
    stolen["identity_document_path"] = "../" + stolen["identity_document_path"]
    assert client.post("/api/applications", headers=auth("bob"), json=stolen).status_code == 422
    assert repo.applications == {}


def test_db_failure_does_not_leak_data(client, repo):
    repo.add_user("alice")
    repo.fail_create = True
    res = apply(client, repo)
    assert res.status_code == 503
    assert "12345678901" not in res.text
