from pathlib import Path


def _read(name: str) -> str:
    return Path(__file__).resolve().parents[1].joinpath("frontend", name).read_text(encoding="utf-8")


def test_issuer_dashboard_has_issue_and_revoke_actions():
    html = _read("issuer_dashboard.html")
    assert "Issuer Dashboard" in html
    assert 'id="btn-issue"' in html
    assert 'id="btn-revoke"' in html
    assert "/api/credentials/issue_dni" in html
    assert "/api/credentials/revoke" in html


def test_verifier_dashboard_has_sign_and_verify_flow():
    html = _read("verifier_dashboard.html")
    assert "Verifier Dashboard" in html
    assert "ethers.umd.min.js" in html
    assert 'id="btn-verify"' in html
    assert "wallet.signMessage" in html
    assert "/api/verify_presentation" in html


def test_legacy_frontend_files_are_not_required_anymore():
    portal = _read("frontend_portal.html")
    assert "issuer_dashboard.html" in portal
    assert "verifier_dashboard.html" in portal


def test_issuer_dashboard_uses_runtime_api_base_url():
    html = _read("issuer_dashboard.html")
    assert "apiBaseUrl" in html
    assert "nattech.fib.upc.edu:40570" in html


def test_verifier_dashboard_uses_runtime_api_base_url():
    html = _read("verifier_dashboard.html")
    assert "apiBaseUrl" in html
    assert "nattech.fib.upc.edu:40570" in html
