"""Idempotent GitHub Release upload. Dry-run by default; no force/clobber/deletion.

Use --execute to create/resume a draft, --execute --publish to make it public.
Those flags are mechanics, not substitutes for the user's publication authority.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from video import read, sha, write


def gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--notes", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    if len(args.commit) != 40 or any(c not in "0123456789abcdef" for c in args.commit):
        raise ValueError(
            "Use the full 40-character source commit SHA; GitHub rejects short target_commitish"
        )
    if not args.notes.is_file():
        raise ValueError("A concrete release notes file is required")
    manifest = read(project / "record/master.json")
    if manifest.get("smoke_test"):
        raise ValueError("Offline smoke-test media must not be published as a research video")
    if manifest.get("full_decode") != "pass":
        raise ValueError("Mastered deliverable is not verified")
    expected = read(project / "record/deliverables.json")
    if set(expected) - {
        "video.mp4",
        "audio.mp3",
        "media-assets.zip",
        "subtitles.srt",
        "subtitles.vtt",
    }:
        raise ValueError("Unexpected upload filenames in the deliverable manifest")
    for name, entry in expected.items():
        file = project / "output" / name
        if file.stat().st_size != entry["bytes"] or sha(file) != entry["sha256"]:
            raise ValueError("Deliverable changed since bundle")
    plan = {
        "repo": args.repo,
        "tag": args.tag,
        "commit": args.commit,
        "title": args.title,
        "notes": str(args.notes.resolve()),
        "files": [*expected, "SHA256SUMS"],
        "publish": args.publish,
    }
    print(json.dumps(plan, indent=2))
    if not args.execute:
        return
    actual = json.loads(gh("api", f"repos/{args.repo}/commits/{args.commit}"))["sha"]
    if actual != args.commit:
        raise ValueError("Push the exact reviewed source commit before creating a release")
    # Listing handles draft releases whose tag endpoint may still return 404.
    releases = json.loads(
        gh("release", "list", "--repo", args.repo, "--limit", "100", "--json", "tagName,isDraft")
    )
    found = next((r for r in releases if r["tagName"] == args.tag), None)
    if found is None:
        gh(
            "release",
            "create",
            args.tag,
            "--repo",
            args.repo,
            "--target",
            args.commit,
            "--title",
            args.title,
            "--notes-file",
            str(args.notes.resolve()),
            "--draft",
            "--latest=false",
        )
    current = json.loads(
        gh(
            "release",
            "view",
            args.tag,
            "--repo",
            args.repo,
            "--json",
            "assets,isDraft,targetCommitish,url,body,name",
        )
    )
    if current["targetCommitish"] != args.commit:
        raise ValueError("Existing release targets a different commit; do not retarget it")
    if (
        current["name"] != args.title
        or current["body"].strip() != args.notes.read_text(encoding="utf-8").strip()
    ):
        raise ValueError(
            "Existing release title/notes differ; inspect before uploading or publishing"
        )
    remote = {asset["name"]: asset for asset in current["assets"]}
    for name in [*expected, "SHA256SUMS"]:
        file = project / "output" / name
        if name in remote:
            if (
                remote[name].get("digest") != "sha256:" + sha(file)
                or remote[name]["size"] != file.stat().st_size
            ):
                raise ValueError(f"Remote asset {name} differs; stop instead of clobbering")
        elif current["isDraft"]:
            gh("release", "upload", args.tag, str(file), "--repo", args.repo)
        else:
            raise ValueError("An already public release is incomplete; inspect before editing it")
    uploaded = json.loads(
        gh("release", "view", args.tag, "--repo", args.repo, "--json", "assets,isDraft,url")
    )
    for name, entry in expected.items():
        asset = next(a for a in uploaded["assets"] if a["name"] == name)
        if asset["state"] != "uploaded" or asset.get("digest") != "sha256:" + entry["sha256"]:
            raise ValueError("Server-side SHA-256 verification failed")
    if args.publish and uploaded["isDraft"]:
        gh("release", "edit", args.tag, "--repo", args.repo, "--draft=false", "--latest=false")
    final = json.loads(
        gh(
            "release",
            "view",
            args.tag,
            "--repo",
            args.repo,
            "--json",
            "assets,isDraft,url,targetCommitish",
        )
    )
    if args.publish and final["isDraft"]:
        raise ValueError("Release remains a draft")
    if args.publish:
        ref = json.loads(gh("api", f"repos/{args.repo}/git/ref/tags/{args.tag}"))
        obj = ref["object"]
        if obj["type"] == "tag":
            obj = json.loads(gh("api", f"repos/{args.repo}/git/tags/{obj['sha']}"))["object"]
        if obj["sha"] != args.commit:
            raise ValueError("Published tag points to another commit")
    write(project / "record/publication.json", final)
    print(final["url"])


if __name__ == "__main__":
    main()
