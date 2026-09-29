"""A text result must verify after Git changes checkout line endings."""

from e13_mbse_evidence import _sha256


def test_evidence_text_hash_is_line_ending_independent(tmp_path):
    lf = tmp_path / "lf.csv"
    crlf = tmp_path / "crlf.csv"
    cr = tmp_path / "cr.csv"
    changed = tmp_path / "changed.csv"
    lf.write_bytes(b"architecture,success\nA0,1\n")
    crlf.write_bytes(b"architecture,success\r\nA0,1\r\n")
    cr.write_bytes(b"architecture,success\rA0,1\r")
    changed.write_bytes(b"architecture,success\nA0,0\n")
    assert _sha256(lf) == _sha256(crlf) == _sha256(cr)
    assert _sha256(lf) != _sha256(changed)
