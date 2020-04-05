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
from github import Github, GithubException, Issue, Repository  # type: ignore

from issue_tagging_bot.issue_data import IssueData, MyEncoder, issue_data_files


class RateLimiter:
    def __init__(self, github: Github) -> None:
        self.github = github

    def maybe_wait(self, buffer_amount: int = 10) -> None:
        # get the current limit
        try:
            rate_limit = self.github.get_rate_limit()
        except GithubException as err:
            print(
                f"Got exception in RateLimiter.maybe_wait(): {err}\nsleeping for 30 seconds and trying again...\n"
            )
            sleep(30)
            return self.maybe_wait(buffer_amount=buffer_amount)

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
    def __init__(
        self,
        github: Github,
        repo_str: str = "NixOS/nixpkgs",
        data_dir_str: str = "issue-data",
    ) -> None:
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
        for issue_num, _ in issue_data_files(self.data_dir_str):
            if lowest is None or issue_num < lowest:
                lowest = issue_num

        return lowest

    def create_data_dir(self) -> None:
        Path(self.data_dir_str).mkdir(parents=True, exist_ok=True)

    def save_issue(self, issue_num: int, issue_data: IssueData) -> None:
        path = Path(self.data_dir_str) / f"{issue_num:06}.json"

        issue_data_json = MyEncoder().encode(issue_data)

        with path.open(mode="w") as f:
            f.write(issue_data_json)

    def get_issue_data_and_save_to_file(self, issue_num: int) -> None:
        issue_data: IssueData = self.get_issue_data(issue_num)
        self.save_issue(issue_num, issue_data)

    def get_issue_data(self, issue_num: int) -> IssueData:
        return IssueData.from_issue(self.get_issue(issue_num))

    def get_issue(self, issue_num: int) -> Issue:
        self.rate_limiter.maybe_wait()

        try:
            issue = self.repo.get_issue(issue_num)
        except GithubException as err:
            if err.status == 404:
                print(f"Issue not found: {issue_num}, skipping...")
                return
            else:
                print(
                    f"Got exception in Fetcher.get_issue() while fetching issue number {issue_num}: {err}\nsleeping for 30 seconds and trying again...\n"
                )
                sleep(30)
                return self.get_issue(issue_num=issue_num)

        return issue

    def get_issues_from(self, starting_issue_num: int) -> None:
        for issue_num in range(starting_issue_num, 0, -1):
            if issue_num % 200 == 0:
                print(f"Getting issue number {issue_num}...")
            self.get_issue_data_and_save_to_file(issue_num)

    @classmethod
    def from_env(cls):
        github_api_token: str = os.environ["GITHUB_API_TOKEN"]
        github = Github(github_api_token)
        return cls(github)

    def run(self) -> None:
        self.create_data_dir()
        lowest_issue_num_already_downloaded: Optional[
            int
        ] = self.get_lowest_issue_num_already_downloaded()
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
    fetcher = Fetcher.from_env()
    fetcher.run()


if __name__ == "__main__":
    main()
