#!/usr/bin/env python

import json
import sys
from datetime import datetime, timedelta, timezone
from time import sleep

from github import Github

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, LabelData):
            return o.__dict__
        if isinstance(o, IssueData):
            return o.__dict__
        return super(MyEncoder, self).default(o)

class LabelData():
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @classmethod
    def from_label(cls, label):
        label_data = cls(label.name, label.url)
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
        self.labels = list(map(LabelData.from_label, labels))
        self.comments = comments
        self.closed_at = None if closed_at is None else str(closed_at)
        self.created_at = None if created_at is None else str(created_at)
        self.updated_at = None if updated_at is None else str(updated_at)
        self.is_pull_request  = pull_request is None

    @classmethod
    def from_issue(cls, issue):
        issue_data = cls(issue.id, issue.url, issue.number, issue.state,
                issue.title, issue.body, issue.user.login, issue.user.id,
                issue.labels, issue.comments, issue.closed_at, issue.created_at,
                issue.updated_at, issue.pull_request)
        return issue_data


class RateLimiter():
    def __init__(self, github):
        self.github = github

    def maybe_wait(self):
        # get the current limit
        self.rate_limit = github.get_rate_limit()

        # TODO: Continue writing this...

def main():

    github = Github()

    rate_limiter = RateLimiter(github)

    rate_limit = github.get_rate_limit()
    print(rate_limit)
    print(rate_limit.core)
    print(rate_limit.core.reset)
    print(rate_limit.core.reset.tzinfo)

    reset_time = rate_limit.core.reset
    utc_reset_time = reset_time.replace(tzinfo=timezone.utc)

    sleep_until_time = reset_time + timedelta(minutes = 1)
    utc_sleep_until_time = sleep_until_time.replace(tzinfo=timezone.utc)

    now = datetime.utcnow()
    utc_now = now.replace(tzinfo=timezone.utc)

    sleep_delta = sleep_until_time - now

    print(f"now: {now} (local: {utc_now.astimezone()})")
    print(f"reset_time: {reset_time}")
    print(f"utc_reset_time: {utc_reset_time} (local: {utc_reset_time.astimezone()})")
    print(f"sleep_until_time: {sleep_until_time} (local: {utc_sleep_until_time.astimezone()})")
    print(f"sleep_delta: {sleep_delta}")
    print(f"sleep_delta.seconds: {sleep_delta.seconds}")

    print(f"sleeping for {sleep_delta.seconds} seconds, until {sleep_until_time.astimezone()}...")

    sleep(sleep_delta.seconds)

    print("Woke up and ending.")


    sys.exit()

    repo = github.get_repo("NixOS/nixpkgs")
    l = repo.get_issues(state="all")
    print(l[0])
    first_issue = l[0]


    print(MyEncoder().encode(IssueData.from_issue(l[6])))

    # for i in l:
    #     print()
    #     print(MyEncoder().encode(IssueData.from_issue(i)))

if __name__ == "__main__":
    # execute only if run as a script
    main()
