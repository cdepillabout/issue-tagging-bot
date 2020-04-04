import json
import os
import sys
from pathlib import Path

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, LabelData):
            return o.__dict__
        if isinstance(o, IssueData):
            return o.__dict__
        return super(MyEncoder, self).default(o)


class LabelData:
    def __init__(self, name, url) -> None:
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
    ) -> None:
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

# TODO: What is the return type of this?
def issue_data_files(data_dir: str = "issue-data"):
    # loop over all the files in the data directory
    for f in os.listdir(data_dir):

        # only look at files that have a .json extension
        if f.endswith(".json"):

            # only use the part of the filename that is before the .json extension
            issue_num_str: str = Path(f).stem

            # try to parse the issue number as an int from the filename.
            try:
                issue_num: int = int(issue_num_str)
            except ValueError:
                print(
                    f"file {data_dir}/{f} does not have a file name stem readable as an int"
                )
                continue

            # TODO: Should probably use actual path manipulation functions for this.
            yield f"{data_dir}/{f}"
