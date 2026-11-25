"""Responding to "request information", LGA/ward matching, and one application per NIN."""

import json
from pathlib import Path

import pytest

from app import constants as c
from app.geo import (
    canonical_lga,
    canonical_ward,
    geo_data,
    geo_key,
    lga_match_keys,
    lgas_by_state,
    wards_by_lga,
)
from app.repository import DuplicateIdentificationError

from .conftest import PDF, PNG, apply, auth, valid_details
from .test_admin import review


@pytest.fixture
def team(repo):
    repo.add_user("national", role="national")
    repo.add_user("kano", role="state", state="Kano")
    repo.add_user("nasarawa", role="lga", state="Kano", lga="Nasarawa")
    repo.add_user("gama", role="ward", state="Kano", lga="Nasarawa", ward="Gama")


def submit(client, repo, token="alice", **details):
    repo.add_user(token)
    res = apply(client, repo, token=token, details=valid_details(**details))
    assert res.status_code == 201, res.json()
    return res.json()["id"]


def me(client, token="alice"):
    return client.get("/api/me", headers=auth(token)).json()["application"]


def respond(client, token="alice", note="Here is a clearer copy of my NIN slip.", **paths):
    return client.post(
        "/api/applications/me/respond", headers=auth(token), json={"note": note, **paths}
    )


def replacement_tickets(client, token="alice", **declared):
    return client.post("/api/applications/me/uploads", headers=auth(token), json=declared)


# --- Request information → applicant responds --------------------------------------------------


def test_applicant_response_returns_application_to_the_asking_stage(client, repo, team):
    app_id = submit(client, repo)
    review(client, "kano", app_id)  # → lga_review
    res = review(client, "nasarawa", app_id, "request_information", "Which market do you sell in?")
    assert res.json()["stage"] == c.STAGE_NEEDS_INFO
    # Nobody can act while the applicant is being asked
    assert review(client, "national", app_id).status_code == 409

    res = respond(client, note="Kurmi Market, every weekday.")
    assert res.status_code == 200, res.json()
    assert res.json()["stage"] == c.STAGE_LGA
    assert res.json()["applicant_response"] == "Kurmi Market, every weekday."

    # The reviewer who asked sees the answer and can carry on
    rows = client.get("/api/admin/applications", headers=auth("nasarawa")).json()["items"]
    assert rows[0]["applicant_response"] == "Kurmi Market, every weekday."
    assert review(client, "nasarawa", app_id).json()["stage"] == c.STAGE_WARD

    actions = [h["action"] for h in me(client)["history"]]
    assert actions == ["submitted", "approve", "request_information", "responded", "approve"]
    assert repo.applications[app_id]["returns_to_stage"] is None


def test_response_can_replace_documents(client, repo, team):
    app_id = submit(client, repo)
    old_path = repo.kyc[app_id]["identity_document_path"]
    review(client, "kano", app_id, "request_information", "Your ID scan is unreadable.")

    tickets = replacement_tickets(
        client, identity_document={"content_type": "image/png", "size": 2000}
    )
    assert tickets.status_code == 200, tickets.json()
    uploads = tickets.json()["uploads"]
    assert set(uploads) == {"identity_document"}  # only what was asked for
    new_path = uploads["identity_document"]["path"]
    assert new_path != old_path
    repo.browser_upload(new_path, PNG)

    res = respond(client, identity_document_path=new_path)
    assert res.status_code == 200, res.json()
    assert res.json()["stage"] == c.STAGE_STATE
    assert repo.kyc[app_id]["identity_document_path"] == new_path
    assert old_path not in repo.files  # superseded scan removed
    # National reviewers now get the new document
    kyc = client.get(f"/api/admin/applications/{app_id}/kyc", headers=auth("national")).json()
    assert new_path in kyc["identity_document_url"]


def test_bad_replacement_is_rejected_and_removed(client, repo, team):
    app_id = submit(client, repo)
    review(client, "kano", app_id, "request_information", "New photo please.")
    up = replacement_tickets(
        client, passport_photograph={"content_type": "image/jpeg", "size": 2000}
    ).json()["uploads"]["passport_photograph"]
    repo.browser_upload(up["path"], PDF)  # claims to be a JPEG
    res = respond(client, passport_photograph_path=up["path"])
    assert res.status_code == 415
    assert up["path"] not in repo.files
    assert repo.applications[app_id]["stage"] == c.STAGE_NEEDS_INFO


def test_cannot_respond_unless_asked(client, repo, team):
    assert respond(client, token="nobody").status_code == 401
    repo.add_user("bob")
    assert respond(client, token="bob").status_code == 404
    submit(client, repo)
    assert respond(client).status_code == 409
    assert (
        replacement_tickets(client, identity_document={"content_type": "image/png", "size": 9})
    ).status_code == 409


def test_response_needs_a_note_and_valid_paths(client, repo, team):
    app_id = submit(client, repo)
    review(client, "kano", app_id, "request_information", "Tell us more.")
    assert respond(client, note="").status_code == 422
    assert replacement_tickets(client).status_code == 422  # nothing to replace
    other = submit(client, repo, token="bob", identification_number="10987654321")
    foreign = repo.kyc[other]["identity_document_path"]
    assert respond(client, identity_document_path=foreign).status_code == 422


# --- LGA / ward matching ----------------------------------------------------------------------
# The `team` fixture assigns its LGA and ward reviewers with the portal's earlier spelling
# "Nasarawa"; GRID3 spells Kano's LGA "Nassarawa". Both must keep working.


def test_lga_and_ward_must_be_official_and_are_stored_canonically(client, repo, team):
    repo.add_user("alice")
    bad = apply(client, repo, details=valid_details(lga="Nowhere"))
    assert bad.status_code == 422
    assert "Local Government Area" in bad.json()["detail"]
    # An LGA from another state is refused too
    assert apply(client, repo, details=valid_details(lga="Zaria")).status_code == 422
    # A ward that is not in the chosen LGA is refused
    bad = apply(client, repo, details=valid_details(ward="Gwagwalada"))
    assert bad.status_code == 422
    assert "ward in Nassarawa" in bad.json()["detail"]

    app_id = submit(client, repo, token="bob", lga="  nasarawa ", ward="  HOTORO-north  ")
    record = repo.applications[app_id]
    assert record["lga"] == "Nassarawa"  # earlier spelling accepted, stored as GRID3's
    assert record["ward"] == "Hotoro North"


def test_reviewers_assigned_with_old_spelling_see_new_applications(client, repo, team):
    app_id = submit(client, repo, ward="GAMA ")
    review(client, "kano", app_id)
    review(client, "nasarawa", app_id)
    listed = client.get("/api/admin/applications", headers=auth("gama")).json()
    assert listed["total"] == 1
    assert review(client, "gama", app_id).json()["stage"] == c.STAGE_APPROVED


def test_rows_saved_before_the_switch_still_match(client, repo, team):
    # Saved with the old LGA spelling and a hand-typed ward, before the lists came from GRID3.
    app_id = submit(client, repo)
    repo.applications[app_id].update(lga="Nasarawa", ward="gama ", stage=c.STAGE_LGA)
    repo.add_user("grid3", role="lga", state="Kano", lga="Nassarawa")
    for token in ("nasarawa", "grid3"):
        listed = client.get("/api/admin/applications", headers=auth(token)).json()
        assert listed["total"] == 1, token
    assert review(client, "grid3", app_id).json()["stage"] == c.STAGE_WARD
    assert review(client, "gama", app_id).json()["stage"] == c.STAGE_APPROVED


def test_misspelt_reviewer_assignment_is_refused_not_silently_empty(client, repo):
    repo.add_user("typo", role="lga", state="Kano", lga="Nasarrawa")
    res = client.get("/api/admin/applications", headers=auth("typo"))
    assert res.status_code == 403
    assert "official list" in res.json()["detail"]
    repo.add_user("badward", role="ward", state="Kano", lga="Nassarawa", ward="Gamma")
    res = client.get("/api/admin/applications", headers=auth("badward"))
    assert res.status_code == 403
    assert "ward that is not on the official list" in res.json()["detail"]
    # Case and punctuation differences in the assignment are fine
    repo.add_user("lower", role="ward", state="Kano", lga="nassarawa", ward="hotoro-NORTH")
    assert client.get("/api/admin/applications", headers=auth("lower")).status_code == 200


def test_unlisted_ward_is_kept_as_typed_and_flagged(client, repo):
    app_id = submit(client, repo, ward="  Sabon   Unguwa ", ward_unlisted=True)
    record = repo.applications[app_id]
    assert record["ward"] == "Sabon Unguwa"
    assert record["ward_unlisted"] is True
    me = client.get("/api/me", headers=auth("alice")).json()["application"]
    assert me["ward_unlisted"] is True
    # Too short to be a ward name
    repo.add_user("bob")
    details = valid_details(ward="-", ward_unlisted=True, identification_number="10987654321")
    assert apply(client, repo, token="bob", details=details).status_code == 422


def test_listed_ward_typed_as_unlisted_is_stored_from_the_list(client, repo):
    app_id = submit(client, repo, ward="hotoro north", ward_unlisted=True)
    record = repo.applications[app_id]
    assert (record["ward"], record["ward_unlisted"]) == ("Hotoro North", False)


def test_unlisted_ward_is_reviewed_by_the_lga_reviewer(client, repo, team):
    app_id = submit(client, repo, ward="Sabon Unguwa", ward_unlisted=True)
    review(client, "kano", app_id)
    assert review(client, "nasarawa", app_id).json()["stage"] == c.STAGE_WARD

    # No ward reviewer can match it...
    assert client.get("/api/admin/applications", headers=auth("gama")).json()["total"] == 0
    assert review(client, "gama", app_id).status_code == 404
    # ...so the LGA reviewer sees it flagged and takes the ward stage.
    listed = client.get("/api/admin/applications", headers=auth("nasarawa")).json()
    assert [a["ward_unlisted"] for a in listed["items"]] == [True]
    assert review(client, "nasarawa", app_id).json()["stage"] == c.STAGE_APPROVED


def test_lga_reviewer_cannot_take_the_ward_stage_for_a_listed_ward(client, repo, team):
    app_id = submit(client, repo)
    review(client, "kano", app_id)
    review(client, "nasarawa", app_id)
    assert review(client, "nasarawa", app_id).status_code == 409
    assert review(client, "gama", app_id).json()["stage"] == c.STAGE_APPROVED


def test_ward_too_short_is_rejected(client, repo):
    repo.add_user("alice")
    assert apply(client, repo, details=valid_details(ward="--")).status_code == 422


# --- One application per identification number ------------------------------------------------


def test_same_nin_cannot_apply_twice(client, repo):
    submit(client, repo)
    repo.add_user("bob")
    res = apply(
        client, repo, token="bob", details=valid_details(identification_number="123 4567 8901")
    )
    assert res.status_code == 409
    assert "identification number" in res.json()["detail"]
    assert not any(p.startswith(repo.users["bob"].id) for p in repo.files)  # uploads cleaned up
    # A different number is fine
    assert submit(client, repo, token="carol", identification_number="10987654321")


def test_duplicate_race_is_a_409_not_a_503(client, repo, monkeypatch):
    repo.add_user("alice")

    def raced(record, kyc):
        raise DuplicateIdentificationError

    monkeypatch.setattr(repo, "create_application", raced)
    res = apply(client, repo)
    assert res.status_code == 409
    assert not repo.files


# --- Reference data (GRID3 NGA Operational Wards v4.0) -----------------------------------------


def test_geo_list_covers_every_state_with_grid3_counts():
    data = lgas_by_state()
    assert tuple(data) == c.NORTHERN_STATES
    assert sum(len(v) for v in data.values()) == 419
    assert len(data["Kano"]) == 44 and len(data["FCT Abuja"]) == 6
    wards = {(s, lga): wards_by_lga(s, lga) for s, lgas in data.items() for lga in lgas}
    assert sum(len(w) for w in wards.values()) == 4841
    assert len(wards["Kano", "Nassarawa"]) == 11
    for lgas in data.values():
        assert len({geo_key(lga) for lga in lgas}) == len(lgas)  # keys never collide
    for names in wards.values():
        assert names and len({geo_key(w) for w in names}) == len(names)
    meta = geo_data()["meta"]
    assert meta["licence"] == "CC BY-SA 4.0" and "GRID3" in meta["dataset"]


def test_lga_aliases_resolve_to_one_lga():
    assert canonical_lga("Kano", "KANO municipal") == "Kano Municipal"
    assert canonical_lga("Kaduna", "Nasarawa") is None
    # Every LGA spelling the portal used before GRID3 still resolves.
    for state, old in [
        ("Kano", "Nasarawa"),
        ("Kano", "Garun Mallam"),
        ("FCT Abuja", "Abuja Municipal"),
        ("Adamawa", "Gayuk"),
        ("Benue", "Otukpo"),
        ("Taraba", "Kumi"),
        ("Sokoto", "Wamako"),
        ("Jigawa", "Biriniwa"),
        ("Gombe", "Shongom"),
    ]:
        assert canonical_lga(state, old) is not None, (state, old)
    assert set(lga_match_keys("Kano", "Nassarawa")) == {"nassarawa", "nasarawa"}
    for state, aliases in geo_data()["lga_aliases"].items():
        for alias, lga in aliases.items():
            assert canonical_lga(state, alias) == lga
    assert canonical_ward("Kano", "Nasarawa", "tudun-wada") == "Tudun Wada"
    assert canonical_ward("Kano", "Nasarawa", "Wuse") is None


def test_frontend_copy_of_geo_list_matches():
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "geo.json"
    if not frontend.exists():  # backend-only checkout
        pytest.skip("frontend not present")
    backend = Path(__file__).resolve().parents[1] / "app" / "geo.json"
    assert json.loads(frontend.read_text()) == json.loads(backend.read_text())
