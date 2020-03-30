
from github import Github

g = Github()
repo = g.get_repo("NixOS/nixpkgs")
l = repo.get_issues(state="all")
print(l[0])

