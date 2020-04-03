#!/usr/bin/env python

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import sleep
from typing import Optional

# PyGithub has gotten mypy types, but it has not been released yet:
# https://github.com/PyGithub/PyGithub/pull/1231
from github import Github, Repository # type: ignore


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, LabelData):
            return o.__dict__
        if isinstance(o, IssueData):
            return o.__dict__
        return super(MyEncoder, self).default(o)


class LabelData:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    @classmethod
    def from_label(cls, label):
        label_data = cls(label.name, label.url)
        return label_data


class IssueData:
    def __init__(
        self,
        id_,
        url,
        number,
        state,
        title,
        body,
        user_login,
        user_id,
        labels,
        comments,
        closed_at,
        created_at,
        updated_at,
        pull_request,
    ):
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
        self.is_pull_request = pull_request is None

    @classmethod
    def from_issue(cls, issue):
        issue_data = cls(
            issue.id,
            issue.url,
            issue.number,
            issue.state,
            issue.title,
            issue.body,
            issue.user.login,
            issue.user.id,
            issue.labels,
            issue.comments,
            issue.closed_at,
            issue.created_at,
            issue.updated_at,
            issue.pull_request,
        )
        return issue_data


class RateLimiter:
    def __init__(self, github: Github) -> None:
        self.github = github

    def maybe_wait(self, buffer_amount: int = 10) -> None:
        # get the current limit
        rate_limit = self.github.get_rate_limit()
        remaining = rate_limit.core.remaining

        if remaining < buffer_amount:

            # The time at which the rate limit is reset.
            reset_time = rate_limit.core.reset

            # When to sleep until.  This is just reset_time plus one minute.
            sleep_until_time = reset_time + timedelta(minutes=1)

            # When to sleep until with a UTC timezone set.
            utc_sleep_until_time = sleep_until_time.replace(tzinfo=timezone.utc)

            now = datetime.utcnow()

            # How much time until the the rate limit is reset.
            sleep_delta = sleep_until_time - now

            print(f"github rate limit remaining requests is {remaining},")
            print(f"which is less than the buffer amount: {buffer_amount},")
            print(
                f"so sleeping for {sleep_delta.seconds} seconds, until {utc_sleep_until_time.astimezone()}..."
            )

            sleep(sleep_delta.seconds)


class Fetcher:
    def __init__(self, github: Github, repo_str: str = "NixOS/nixpkgs", data_dir_str: str = "issue-data") -> None:
        self.github = github
        self.rate_limiter = RateLimiter(github)
        self.rate_limiter.maybe_wait()
        self.repo: Repository = github.get_repo(repo_str)
        self.data_dir_str = data_dir_str

    def get_highest_issue_num(self) -> int:
        self.rate_limiter.maybe_wait()
        all_issues = self.repo.get_issues(state="all")
        return all_issues.totalCount

    def get_lowest_issue_num_already_downloaded(self) -> Optional[int]:
        lowest: Optional[int] = None

        # loop over all the files in the data directory
        for f in os.listdir(self.data_dir_str):

            # only look at files that have a .json extension
            if f.endswith(".json"):

                # only use the part of the filename that is before the .json extension
                issue_num_str: str = Path(f).stem

                # try to parse the issue number as an int from the filename.
                try:
                    issue_num: int = int(issue_num_str)
                except ValueError:
                    print(f"file {self.data_dir_str}/{f} does not have a file name stem readable as an int")
                    continue

                if lowest is None or issue_num < lowest:
                    lowest = issue_num

        return lowest

    def create_data_dir(self) -> None:
        Path(self.data_dir_str).mkdir(parents=True, exist_ok=True)

    def save_issue(self, issue_num: int, issue_data: IssueData) -> None:
        path = Path(self.data_dir_str) / f"{issue_num}.json"

        issue_data_json = MyEncoder().encode(issue_data)

        with path.open(mode="w") as f:
            f.write(issue_data_json)

    def get_issue(self, issue_num: int) -> None:
        self.rate_limiter.maybe_wait()
        issue = self.repo.get_issue(issue_num)
        issue_data: IssueData = IssueData.from_issue(issue)
        if not issue_data.is_pull_request:
            self.save_issue(issue_num, issue_data)

    def get_issues_from(self, starting_issue_num: int) -> None:
        for issue_num in range(starting_issue_num, 0, -1):
            self.get_issue(issue_num)

    def run(self) -> None:
        self.create_data_dir()
        lowest_issue_num_already_downloaded: Optional[int] = self.get_lowest_issue_num_already_downloaded()
        start_issue_num: int

        if lowest_issue_num_already_downloaded is None:
            start_issue_num = self.get_highest_issue_num()
        elif lowest_issue_num_already_downloaded <= 1:
            print("Already downloaded all issues! Ending.")
            sys.exit(0)
        else:
            start_issue_num = lowest_issue_num_already_downloaded - 1

        print(f"Starting with issue number: {start_issue_num}")

        self.get_issues_from(start_issue_num)



def main() -> None:

    github = Github()

    fetcher = Fetcher(github)
    fetcher.run()

    # repo: Repository = github.get_repo("NixOS/nixpkgs")
    # l = repo.get_issues(state="all")
    # print(l[0])
    # first_issue = l[0]

    # print(MyEncoder().encode(IssueData.from_issue(l[6])))

    # for i in l:
    #     print()
    #     print(MyEncoder().encode(IssueData.from_issue(i)))


if __name__ == "__main__":
    # execute only if run as a script
    main()
