from lib.versions import extract_youtube_versions, pick_latest_version, to_apkmirror_version


def test_extract_versions_from_section():
    output = """
    Some noise before

    Most common compatible versions:
    19.16.39 (25 patches)
    19.09.37 (18 patches)
    18.20.39 (5 patches)

    trailing noise
    """
    result = extract_youtube_versions(output)
    assert result == [
        {"version": "19.16.39", "patches": 25},
        {"version": "19.09.37", "patches": 18},
        {"version": "18.20.39", "patches": 5},
    ]


def test_extract_versions_fallback_when_no_section():
    output = "random text mentioning 1.2.3 and 4.5.6 with no proper section"
    result = extract_youtube_versions(output)
    assert {"version": "1.2.3", "patches": 0} in result
    assert {"version": "4.5.6", "patches": 0} in result


def test_pick_latest_prefers_more_patches_over_raw_version():
    # This is the exact bug class we fixed before: a numerically "newer"
    # version with fewer supported patches should lose to an older version
    # backed by more patches, since that's what actually gets more features enabled.
    versions = [
        {"version": "19.20.00", "patches": 3},
        {"version": "19.16.39", "patches": 25},
    ]
    assert pick_latest_version(versions) == "19.16.39"


def test_pick_latest_breaks_ties_by_version_number():
    versions = [
        {"version": "18.20.39", "patches": 25},
        {"version": "19.16.39", "patches": 25},
    ]
    assert pick_latest_version(versions) == "19.16.39"


def test_pick_latest_returns_none_for_empty_list():
    assert pick_latest_version([]) is None


def test_pick_latest_handles_prerelease_suffix():
    versions = [
        {"version": "19.16.39-beta.1", "patches": 10},
        {"version": "19.16.39", "patches": 10},
    ]
    # both have equal core version + patch count; just shouldn't crash
    assert pick_latest_version(versions) in ("19.16.39-beta.1", "19.16.39")


def test_to_apkmirror_version_replaces_dots_with_dashes():
    assert to_apkmirror_version("19.16.39") == "19-16-39"
