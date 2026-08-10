"""Where things get downloaded from: base APKs and patch bundles.

Previously this was split across `lib/apkmirror.py` (APP_SITES),
`lib/githubdl.py` (APP_TAGS) and `lib/config.py` (PATCH_SOURCES / the
APKMIRROR_APPS name list). Keeping it all in one config file means adding
a new app's download source is a one-stop edit instead of three.
"""

from __future__ import annotations

from typing import TypedDict


class ApkMirrorSite(TypedDict, total=False):
    org: str
    slug: str
    release_slug: str  # only needed when it differs from `slug`


# Apps whose base APK is scraped from APKMirror (via lib/apkmirror).
APKMIRROR_SITES: dict[str, ApkMirrorSite] = {
    "youtube": {"org": "google-inc", "slug": "youtube"},
    "youtube-music": {"org": "google-inc", "slug": "youtube-music"},
    "reddit": {"org": "reddit-inc", "slug": "reddit"},
    "twitter": {"org": "x-corp", "slug": "twitter", "release_slug": "x"},
    "instagram": {"org": "instagram", "slug": "instagram"},
    "gboard": {"org": "google-inc", "slug": "gboard", "release_slug": "gboard-the-google-keyboard"},
    "speedtest": {"org": "ookla", "slug": "speedtest"},
    "brave": {"org": "brave-software", "slug": "brave-browser", "release_slug": "brave-private-web-browser-vpn"},
    "proton-vpn": {
        "org": "proton-technologies-ag",
        "slug": "protonvpn-secure-and-free-vpn",
        "release_slug": "proton-vpn-fast-secure-vpn",
    },
    "tiktok": {"org": "tiktok-pte-ltd", "slug": "tik-tok-including-musical-ly", "release_slug": "tiktok"},
    "warp": {
        "org": "cloudflare",
        "slug": "1-1-1-1-faster-safer-internet",
        "release_slug": "1-1-1-1-warp-safer-internet",
    },
    "inshot": {
        "org": "inshot-inc",
        "slug": "inshot-video-editor-photo-editor",
        "release_slug": "video-editor-maker-inshot",
    },
    "google-photos": {"org": "google-inc", "slug": "photos", "release_slug": "google-photos"},
}

# Apps whose base APK is instead pulled from a GitHub release (mirrored by us),
# keyed by app -> release tag in the fuckpdf/Depo mirror repo.
GITHUB_SOURCE_TAGS: dict[str, str] = {
    "instagram": "instagram",
    "speedtest": "Speedtest",
}

APKMIRROR_APPS: list[str] = list(APKMIRROR_SITES.keys())

# owner, repo, human label - where each patch bundle (.mpp) is downloaded from.
PATCH_SOURCES: dict[str, tuple[str, str, str]] = {
    "morphe": ("MorpheApp", "morphe-patches", "Morphe"),
    "piko": ("crimera", "piko", "Piko"),
    "adobo": ("jkennethcarino", "adobo", "Adobo"),
    "rushi": ("rushiranpise", "morphe-patches", "Rushiranpise"),
    "bufferk": ("bufferk", "morphe-patches", "Bufferk"),
    "hoodles": ("hoo-dles", "morphe-patches", "hoo-dles"),
    "tiktok": ("icysymmetra", "tiktok-patches-for-morphe", "TikTok Patches"),
    "hooman": ("arandomhooman", "hoomans-morphe-patches", "Hooman's Patches"),
    "jasonwu": ("jasonwu1994", "Gboard-patches", "Gboard Patches"),
}
