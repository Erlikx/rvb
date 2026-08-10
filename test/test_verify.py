import json

from lib.verify import _DIGEST_RE, _load_json, _save_json


def test_digest_regex_extracts_fingerprint_from_apksigner_output():
    sample_output = (
        "Verifies\n"
        "Verified using v2 scheme (APK Signature Scheme v2): true\n"
        "Signer #1 certificate DN: CN=Example\n"
        "Signer #1 certificate SHA-256 digest: aa:bb:cc:dd:ee:ff:00:11\n"
    )
    matches = _DIGEST_RE.findall(sample_output)
    assert matches == ["aa:bb:cc:dd:ee:ff:00:11"]


def test_load_json_returns_empty_dict_for_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    assert _load_json(missing) == {}


def test_load_json_returns_empty_dict_for_corrupt_file(tmp_path):
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not valid json")
    assert _load_json(corrupt) == {}


def test_save_and_reload_json_round_trip(tmp_path):
    path = tmp_path / "signatures.json"
    data = {"youtube": "abc123", "reddit": "def456"}

    _save_json(path, data)

    assert json.loads(path.read_text()) == data
    assert _load_json(path) == data
