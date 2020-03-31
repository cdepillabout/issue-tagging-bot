#!/usr/bin/env python

import json

from github import Github

g = Github()
repo = g.get_repo("NixOS/nixpkgs")
l = repo.get_issues(state="all")
print(l[0])
first_issue = l[0]

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, LabelData):
            print("LLLLLLLLLLLLLLLLLLLLLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            return o.__dict__
        if isinstance(o, IssueData):
            return o.__dict__
        return super(MyEncoder, self).default(o)

class LabelData():
    def __init__(self, name, url):
        self.name = name
        self.url = url

def label_to_label_data(label):
    label_data = LabelData(label.name, label.url)
    return label_data

class IssueData():
    def __init__(self, id_, url, number, state, title, body,
            user_login, user_id, labels, comments, closed_at, created_at,
            updated_at, pull_request):
        self.id = id_
        self.url = url
        self.number = number
        self.state = state
        self.title = title
        self.body = body
        self.user_login = user_login
        self.user_id = user_id
        self.labels = list(map(label_to_label_data, labels))
        self.comments = comments
        self.closed_at = None if closed_at is None else str(closed_at)
        self.created_at = None if created_at is None else str(created_at)
        self.updated_at = None if updated_at is None else str(updated_at)
        self.is_pull_request  = pull_request is None

def issue_to_issue_data(issue):
    issue_data = IssueData(issue.id, issue.url, issue.number, issue.state,
            issue.title, issue.body, issue.user.login, issue.user.id,
            issue.labels, issue.comments, issue.closed_at, issue.created_at,
            issue.updated_at, issue.pull_request)
    return issue_data

# print(first_issue.pull_request)
# print(l[1].pull_request)
# print(l[2].pull_request)
# print(l[3].pull_request)
# print(l[4].pull_request)
# print(l[5].pull_request)
# print(l[6].pull_request)

issue_data = issue_to_issue_data(first_issue)
# print(json.dumps(issue_data.__dict__))
# print(MyEncoder().encode(issue_data))
# print(json.dumps(.__dict__))
print(MyEncoder().encode(issue_to_issue_data(l[6])))

for i in l:
    print()
    print(MyEncoder().encode(issue_to_issue_data(i)))
