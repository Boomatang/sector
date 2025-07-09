import logging
import os
from dataclasses import dataclass, field
from typing import Any

import requests
from rich import print
from rich.progress import track

log: logging.Logger
TIMEOUT = 30


@dataclass
class PrData:
    title: str
    url: str


@dataclass
class ReleaseData:
    name: str = ""
    tag: str = ""
    date: str = ""
    url: str = ""
    commit_count: int = 0
    prs: list[PrData] = field(default_factory=list)


@dataclass
class Data:
    owner: str
    project: str
    github: ReleaseData


@dataclass
class Repo:
    name: str
    tag: str | None

    def __init__(self, project: str) -> None:
        _project = project.split("@")
        self.name = _project[0]
        self.tag = _project[1] if 1 < len(_project) else None

    def __repr__(self) -> str:
        tag = f"@{self.tag}" if self.tag is not None else ""
        return f"{self.name}{tag}"


def info(
    owner: str,
    repos: list[Repo],
    logger: logging.Logger,
    _sort: str,
    detailed: bool,
) -> None:
    global log
    log = logger
    log.info("starting run")
    data = []
    for repo in track(repos, description="Processing..."):
        data.append(process_repo(owner, repo, detailed))
    if _sort == "time":
        data.sort(key=lambda d: d.github.date)
    new = False
    print()
    for item in data:
        print_data(item, new=new, detailed=detailed)
        if _sort == "time" and item.project == "kuadrant-operator":
            # TODO: Need a better way of doing this for when the sort is not time based.
            new = True


def set_headers() -> dict[str, str]:
    github_token = os.getenv("GITHUB_TOKEN", "")
    if len(github_token) == 0:
        raise ValueError("GITHUB_TOKEN not set")
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_release(owner: str, repo: Repo) -> ReleaseData:
    global log
    log.info(f"Getting release data for {owner}/{repo}")
    version = "latest" if repo.tag is None else f"tags/{repo.tag}"
    url = f"https://api.github.com/repos/{owner}/{repo.name}/releases/{version}"
    response = requests.get(url, headers=set_headers(), timeout=TIMEOUT)
    response.raise_for_status()
    release = response.json()
    if not release:
        print("No releases found.")
        log.warning("no releases found")
        return ReleaseData()

    name = release.get("name", "No title")
    tag = release.get("tag_name", "No tag")
    date = release.get("published_at", "No date")
    url = release.get("html_url", "No URL")
    release_data = ReleaseData(name=name, tag=tag, date=date, url=url)
    log.debug(f"{release_data=}")
    return release_data


def get_commits_between(owner: str, repo: str, base: str, head: str) -> list[str]:
    global log
    log.info(f"Getting commits for {owner}/{repo} {base}...{head}")
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
    response = requests.get(url, headers=set_headers(), timeout=TIMEOUT)
    response.raise_for_status()
    commits = [commit["sha"] for commit in response.json()["commits"]]
    log.debug(f"{commits=}")
    return commits


def find_prs_for_commit(owner: str, repo: str, sha: str) -> Any:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/pulls"
    response = requests.get(url, headers=set_headers(), timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def list_pr_commits(url: str) -> list[str]:
    response = requests.get(url, headers=set_headers(), timeout=TIMEOUT)
    response.raise_for_status()
    return [commit["sha"] for commit in response.json()]


def process_repo(owner: str, repo: Repo, detailed: bool = False) -> Data:
    global log
    log.info(f"Processing data for {owner}/{repo}")

    github = get_release(owner, repo)
    if github is not None:
        data = Data(owner=owner, project=repo.name, github=github)
    if detailed:
        base = repo.tag if repo.tag is not None else data.github.tag
        sha_list = get_commits_between(owner, repo.name, base, "main")
        data.github.commit_count = len(sha_list)
        seen = []
        for sha in sha_list:
            prs = find_prs_for_commit(owner, repo.name, sha)
            for pr in prs:
                if pr["id"] in seen:
                    break
                seen.append(pr["id"])
                prData = PrData(title=pr["title"], url=pr["html_url"])

                data.github.prs.append(prData)
    return data


def new_string(new: bool) -> str:
    if new:
        return "[bold red]NEW[/bold red]"
    return ""


def print_data(data: Data, new: bool = False, detailed: bool = False) -> None:
    if detailed:
        print(
            f"Project: {data.owner}/{data.project}"
            f"\nRelease: {data.github.name} ({data.github.tag}) {new_string(new)}"
            f"\nReleased: {data.github.date}"
            f"\nURL: {data.github.url}"
            f"\nTotal PRs ahead on main: {len(data.github.prs)}"
            f"({data.github.commit_count} commits)"
        )
        for pr in data.github.prs:
            print(f"-  {pr.title}\n   {pr.url}")

        print()
    else:
        print(f"{data.owner}/{data.project} {data.github.name} {new_string(new)}")
