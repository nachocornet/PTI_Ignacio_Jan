from pathlib import Path


def _frontend_html() -> str:
    return Path(__file__).resolve().parents[1].joinpath("frontend.html").read_text(encoding="utf-8")


def test_frontend_has_main_sections_and_actions():
    html = _frontend_html()
    assert "SSI v2 Control Center" in html
    assert 'id="btn-load-wallet"' in html
    assert 'id="btn-issue"' in html
    assert 'id="btn-verify"' in html
    assert 'id="btn-revoke"' in html
    assert 'id="activity-log"' in html
    assert 'id="payload-view"' in html


def test_frontend_has_real_signature_flow():
    html = _frontend_html()
    assert "ethers.umd.min.js" in html
    assert "async function buildSignedVP" in html
    assert "state.wallet.signMessage" in html
    assert "proofValue" in html


def test_frontend_has_responsive_and_feedback_elements():
    html = _frontend_html()
    assert "@media (max-width: 760px)" in html
    assert "id=\"banner\"" in html
    assert "setBanner(" in html
    assert "refreshConnections" in html
