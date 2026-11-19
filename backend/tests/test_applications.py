import json

from .conftest import PNG, auth, files, valid_details


def submit(client, token="alice", details=None, **file_kwargs):
    return client.post(
        "/api/applications",
        headers=auth(token),
        data={"details": json.dumps(details or valid_details())},
        files=files(**file_kwargs),
    )


def test_requires_authentication(client):
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", headers=auth("nobody")).status_code == 401


def test_me_without_application(client, repo):
    repo.add_user("alice")
    body = client.get("/api/me", headers=auth("alice")).json()
    assert body["profile"]["role"] == "applicant"
    assert body["application"] is None


def test_submit_and_track(client, repo):
    repo.add_user("alice")
    res = submit(client)
    assert res.status_code == 201, res.text
    ref = res.json()["reference"]
    assert ref.startswith("ARP-")
    assert len(repo.files) == 2

    me = client.get("/api/me", headers=auth("alice")).json()
    assert me["application"]["reference"] == ref
    assert me["application"]["stage"] == "state_review"
    assert me["application"]["history"][0]["action"] == "submitted"
    # KYC never appears in applicant views
    assert "identification_number" not in json.dumps(me)
    app_id = me["application"]["id"]
    assert repo.kyc[app_id]["identification_number"] == "12345678901"
    assert "identification_number" not in repo.applications[app_id]


def test_one_application_per_user(client, repo):
    repo.add_user("alice")
    assert submit(client).status_code == 201
    assert submit(client).status_code == 409


def test_email_verification_required(client, repo):
    repo.add_user("alice", verified=False)
    assert submit(client).status_code == 403


def test_validation_errors(client, repo):
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
    ]
    for details in cases:
        res = submit(client, details=details)
        assert res.status_code == 422, (details, res.text)
    assert repo.applications == {}


def test_passport_number_normalised(client, repo):
    repo.add_user("alice")
    res = submit(
        client,
        details=valid_details(
            identification_type="International Passport", identification_number="a 12345678"
        ),
    )
    assert res.status_code == 201
    assert next(iter(repo.kyc.values()))["identification_number"] == "A12345678"


def test_rejects_wrong_file_types(client, repo):
    repo.add_user("alice")
    assert submit(client, identity=b"not a real file").status_code == 415
    # PDF is not allowed for the passport photograph
    assert submit(client, photo=b"%PDF-1.4 data").status_code == 415
    assert submit(client, photo=PNG).status_code == 201


def test_rejects_large_files(client, repo, settings):
    settings.max_upload_bytes = 100
    repo.add_user("alice")
    assert submit(client, identity=b"%PDF-" + b"0" * 200).status_code == 413


def test_cleans_up_uploads_on_failure(client, repo):
    repo.add_user("alice")
    repo.fail_create = True
    res = submit(client)
    assert res.status_code == 503
    assert "12345678901" not in res.text
    assert repo.files == {}
