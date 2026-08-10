"""Human-facing names and icons, used for the final .apk filename and the
release notes body. Purely cosmetic - never affects patching logic."""

from __future__ import annotations

DISPLAY_NAMES: dict[str, str] = {
    "youtube": "YouTube",
    "youtube-music": "YT.Music",
    "reddit": "Reddit",
    "twitter": "Twitter",
    "instagram": "Instagram",
    "gboard": "Gboard",
    "speedtest": "Speedtest",
    "brave": "Brave",
    "proton-vpn": "Proton VPN",
    "tiktok": "TikTok",
    "warp": "1.1.1.1",
    "inshot": "InShot",
    "google-photos": "Google Photos",
}

ICONS: dict[str, str] = {
    "youtube": "https://cdn.simpleicons.org/youtube/FF0000",
    "youtube-music": "https://cdn.simpleicons.org/youtubemusic/FF0000",
    "reddit": "https://cdn.simpleicons.org/reddit/FF4500",
    "twitter": "https://cdn.simpleicons.org/x/000000",
    "instagram": "https://cdn.simpleicons.org/instagram/E4405F",
    "gboard": "https://cdn.simpleicons.org/google/4285F4",
    "speedtest": "https://www.google.com/s2/favicons?sz=128&domain=speedtest.net",
    "brave": "https://cdn.simpleicons.org/brave/FB542B",
    "proton-vpn": "https://cdn.simpleicons.org/protonvpn",
    "tiktok": "https://cdn.simpleicons.org/tiktok",
    "warp": "https://cdn.simpleicons.org/1dot1dot1dot1",
    "inshot": "https://www.google.com/s2/favicons?sz=128&domain=inshot.com",
    "google-photos": "https://cdn.simpleicons.org/googlephotos",
}


def display_name(app_key: str) -> str:
    return DISPLAY_NAMES.get(app_key, app_key)


def icon(app_key: str) -> str:
    return ICONS.get(app_key, "")
