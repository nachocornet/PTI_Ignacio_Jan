from pathlib import Path


def _read(name: str) -> str:
    return Path(__file__).resolve().parents[1].joinpath("frontend", name).read_text(encoding="utf-8")


def test_frontend_portal_links_to_split_uis():
    html = _read("frontend_portal.html")
    assert "issuer_dashboard.html" in html
    assert "verifier_dashboard.html" in html


def test_issuer_dashboard_has_issue_and_revoke_actions():
    html = _read("issuer_dashboard.html")
    assert 'id="btn-issue"' in html
    assert 'id="btn-revoke"' in html
    assert "/api/credentials/issue_dni" in html
    assert "/api/credentials/revoke" in html


def test_verifier_dashboard_has_sign_and_verify_flow():
    html = _read("verifier_dashboard.html")
    assert "ethers.umd.min.js" in html
    assert 'id="btn-verify"' in html
    assert "wallet.signMessage" in html
    assert "/api/verify_presentation" in html
