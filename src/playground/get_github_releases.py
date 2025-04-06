import os

import requests
from rich import print


def set_headers():
    github_token = os.getenv("GITHUB_TOKEN", "")
    if github_token == "":
        raise ValueError("GITHUB_TOKEN not set")
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_latest_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url, headers=set_headers())
    response.raise_for_status()
    release = response.json()
    if not release:
        print("No releases found.")
        return

    name = release.get("name", "No title")
    tag = release.get("tag_name", "No tag")
    date = release.get("published_at", "No date")
    url = release.get("html_url", "No URL")
    return {"name": name, "tag": tag, "date": date, "url": url, "prs": []}


def get_commits_between(owner, repo, base, head):
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
    response = requests.get(url, headers=set_headers())
    response.raise_for_status()
    return [commit["sha"] for commit in response.json()["commits"]]


def find_prs_for_commit(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}/pulls"
    response = requests.get(url, headers=set_headers())
    response.raise_for_status()
    return response.json()


def list_pr_commits(url):
    response = requests.get(url, headers=set_headers())
    response.raise_for_status()
    return [commit["sha"] for commit in response.json()]


def image_exists(owner, repo, tag):
    url = f"https://quay.io/api/v1/repository/{owner}/{repo}/tag/"
    response = requests.get(url, params={"specificTag": tag})
    response.raise_for_status()
    data = response.json()
    if len(data["tags"]) == 1:
        return True

    return False


def process_repo(owner, repo):
    data = {
        "owner": owner,
        "project": repo,
    }
    data["github"] = get_latest_releases(owner, repo)
    sha_list = get_commits_between(owner, repo, data["github"]["tag"], "main")
    seen = []
    for sha in sha_list:
        if sha in seen:
            break
        prs = find_prs_for_commit(owner, repo, sha)
        for pr in prs:
            if pr["id"] in seen:
                break
            seen.extend(list_pr_commits(pr["commits_url"]))
            seen.append(pr["id"])
            data["github"]["prs"].append({"title": pr["title"], "url": pr["html_url"]})
    print_data(data)


def print_data(data):
    print(
        f"Project: {data['owner']}/{data['project']}"
        f"\nRelease: {data['github']['name']} ({data['github']['tag']})"
        f"\nReleased: {data['github']['date']}"
        f"\nURL: {data['github']['url']}"
        f"\nTotal PRs ahead on main: {len(data['github']['prs'])}"
    )
    for pr in data["github"]["prs"]:
        print(f"-  {pr['title']}\n   {pr['url']}")

    print()


if __name__ == "__main__":
    owner = "kuadrant"
    repos = [
        "authorino",
        "authorino-operator",
        "dns-operator",
        "kuadrant-operator",
        "kuadrantctl",
        "limitador",
        "limitador-operator",
    ]
    for repo in repos:
        process_repo(owner, repo)

    # print(data)
