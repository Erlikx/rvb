"""Per-app patch configuration: package name, architecture, which patches
to enable/disable, and any version/build pinning.

This is the file you touch when adding a new app to patch, or tweaking
which ReVanced-style patches are on/off for an existing one.
"""

from __future__ import annotations

from typing import TypedDict


class AppPatchConfig(TypedDict, total=False):
    pkg: str
    patch_source: str
    arch: str
    exclude: list[str]
    enable: list[str]
    force_version: str
    force_build: str


APPS_CONFIG: dict[str, AppPatchConfig] = {
    "youtube": {
        "pkg": "com.google.android.youtube",
        "patch_source": "morphe",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "youtube-music": {
        "pkg": "com.google.android.apps.youtube.music",
        "patch_source": "morphe",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "reddit": {
        "pkg": "com.reddit.frontpage",
        "patch_source": "morphe",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "twitter": {
        "pkg": "com.twitter.android",
        "patch_source": "piko",
        "arch": "arm64-v8a",
        "exclude": ["Dynamic color"],
        "enable": ["Bring back twitter", "Disunify xchat system", "Export all activities"],
    },
    "instagram": {
        "pkg": "com.instagram.android",
        "patch_source": "piko",
        "arch": "arm64-v8a",
        "exclude": [],
        "enable": [],
        "force_version": "435.0.0.37.76",
        "force_build": "384109456",
    },
    "gboard": {
        "pkg": "com.google.android.inputmethod.latin",
        "patch_source": "jasonwu",
        "arch": "arm64-v8a",
        "exclude": [],
        "force_version": "17.7.7.932364120",
        "enable": [
            "AI Writing Tools", "Add Gboard Signature Bypass", "Advanced Voice Typing",
            "Clipboard Custom Character Limit", "Clipboard Enhancements", "Custom Symbols",
            "Developer options", "Emojis, stickers & GIFs Tab Order", "Enable Inline Autofill Suggestions",
            "Enable OCR / Scan Text", "English QWERTY Up-Flick Uppercase", "Grammar Checker",
            "Inline Suggestions", "Key Shape Selection", "Latin Globe Key Ignore Interval",
            "Long-Press Editing Shortcuts", "Package Rename", "Settings Homepage Override",
            "Swipeable Custom Top Row", "Use Bluetooth Microphone", "Web Clipboard",
            "Zhuyin Bottom Row Key Sizes", "Zhuyin Quick Traditional/Simplified Toggle", "Zhuyin Slide Input",
        ],
    },
    "speedtest": {
        "pkg": "org.zwanoo.android.speedtest",
        "patch_source": "rushi",
        "arch": "arm64-v8a",
        "exclude": [],
        "force_version": "7.0.7",
    },
    "brave": {
        "pkg": "com.brave.browser",
        "patch_source": "bufferk",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "proton-vpn": {
        "pkg": "ch.protonvpn.android",
        "patch_source": "hoodles",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "tiktok": {
        "pkg": "com.zhiliaoapp.musically",
        "patch_source": "tiktok",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "warp": {
        "pkg": "com.cloudflare.onedotonedotonedotone",
        "patch_source": "rushi",
        "arch": "arm64-v8a",
        "exclude": [],
        "enable": ["Disable SSL Pinning"],
    },
    "inshot": {
        "pkg": "com.camerasideas.instashot",
        "patch_source": "hooman",
        "arch": "arm64-v8a",
        "exclude": [],
    },
    "google-photos": {
        "pkg": "com.google.android.apps.photos",
        "patch_source": "rushi",
        "arch": "arm64-v8a",
        "force_version": "7.86.0.956040398",
        "exclude": [],
        "enable": [
            "AMOLED dark theme", "Change package name", "Enable DCIM folders backup control",
            "Fix DCIM folder classification", "Spoof features", "GmsCore support",
        ],
    },
}

PROCESS_ORDER: list[str] = [
    "youtube", "youtube-music", "reddit", "twitter", "instagram",
    "gboard", "speedtest", "brave",
    "proton-vpn", "tiktok", "warp", "inshot", "google-photos",
]
