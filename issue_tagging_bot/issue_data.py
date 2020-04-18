import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Tuple

from github import Issue  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore
import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import tensorflow as tf  # type: ignore


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
        self.is_issue = pull_request is None

    @classmethod
    def from_issue(cls, issue: Issue):
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


class IssueFiles:
    """
    This class contains helpful functions for operating on the issue data that
    has been downloaded from GitHub.  The most important function is
    issue_data_frame, which returns a DataFrame containing the data from all
    downloaded issues (not PRs).
    """

    def __init__(self, data_dir: str = "issue-data") -> None:
        self.data_dir = data_dir

    def files(self) -> Iterator[Tuple[int, Path]]:
        """
        Return an iterator containing tuples of issue numbers and paths to the
        json file for that issue.
        """
        # loop over all the files in the data directory
        for f in sorted(os.listdir(self.data_dir)):

            # only look at files that have a .json extension
            if f.endswith(".json"):

                # only use the part of the filename that is before the .json extension
                issue_num_str: str = Path(f).stem

                # try to parse the issue number as an int from the filename.
                try:
                    issue_num: int = int(issue_num_str)
                except ValueError:
                    print(
                        f"file {self.data_dir}/{f} does not have a file name stem readable as an int"
                    )
                    continue

                # TODO: Should probably use actual path manipulation functions for this.
                yield issue_num, Path(f"{self.data_dir}/{f}")

    def raws(self) -> Iterator[str]:
        """
        Return an iterator of raw json files for each issue.
        """
        for _, path in self.files():
            with open(path, "r") as f:
                yield f.read()

    def data_frames(self) -> Iterator[pd.DataFrame]:
        """
        Return a DataFrame for each raw json issue.
        """
        for raw_json in self.raws():
            yield pd.read_json(f"[{raw_json}]", orient="records")

    def data_frame(self) -> pd.DataFrame:
        """
        Return a single dataframe containing info from all issues.
        """
        all_raws = ",".join(self.raws())
        final_raw_str = f"[{all_raws}]"
        all_data: pd.DataFrame = pd.read_json(final_raw_str, orient="records")
        return all_data

    def issues_data_frame(self) -> pd.DataFrame:
        """
        Return a single dataframe containing data ONLY from issues (not PRs).

        This returns a dataframe of shape (NUM_ISSUES, 14).

        The row indicies are issue numbers (so they do not go from 1...NUM_ISSUES).
        """
        all_issues = self.data_frame()
        return all_issues[all_issues.is_issue]


class Stage1PreprocData:
    """
    This is the first stage of prepocessing the issue data.  The topic labels
    we care about are pulled out into one-hot-encoded columns.
    """

    def __init__(self) -> None:
        issue_files = IssueFiles()

        # Get a single dataframe with only issues data.
        # The row indicies are non-sequential, and sort of correspond to
        # issues numbers on GitHub, but are slightly different.
        only_issues: pd.DataFrame = issue_files.issues_data_frame()

        # Create a series that has the labels on each issue.  This returns a Series
        # that is NUM_LABELS long (normally around 100 labels).
        label_series: pd.Series = only_issues.labels.apply(
            lambda val: set(map(lambda l: l["name"], val))
        )

        mlb: MultiLabelBinarizer = MultiLabelBinarizer()

        # This is a one-hot-encoded numpy array with ones for each label.  This is
        # of size (NUM_ISSUES, NUM_LABELS).  Normally around (15000, 100).
        one_hot_labels: np.ndarray = mlb.fit_transform(label_series)

        # This is a boolean array with True for each label that starts with "6.".
        # These are the topic labels we want to be able to predict, like "Haskell",
        # "QT", "Rust", etc.  This is of shape (NUM_LABELS,).
        topic_label_selector: np.ndarray = np.char.startswith(
            mlb.classes_.astype(str), "6."
        )

        # This is a string array that contains only the labels that start with
        # "6.".  This is of shape (NUM_TOPIC_LABELS,).  Normally around (50,).
        topic_classes: np.ndarray = mlb.classes_[topic_label_selector]

        # This is a one-hot array with a 1 for each issue that has a given
        # topic-label.  This is of shape (NUM_ISSUES, NUM_TOPIC_LABELS).  Normally
        # around (15000, 50).
        topic_labels: np.ndarray = one_hot_labels[:, topic_label_selector]

        # A DataFrame where the rows are all an index from 0 to NUM_ISSUES, and
        # the columns are topic labels.  This is of shape (NUM_ISSUES,
        # NUM_TOPIC_LABELS).  Normally around (15000, 50).
        topics: pd.DataFrame = pd.DataFrame(data=topic_labels, columns=topic_classes)

        # A list of indicies of only the issues.
        only_issues_indicies: pd.Int64Index = only_issues.index

        # This is the same as topics above, but the indicies are almost the indicies of
        # the actual issues on GitHub (not 0 to NUM_ISSUES), but are slightly off in
        # certain cases.
        topics_with_index: pd.DataFrame = topics.set_index(only_issues_indicies)

        # This is the same as only_issues, but it has all the one-hot-encoded
        # topic labels as columns as well.
        only_issues_with_labels: pd.DataFrame = pd.concat(
            [only_issues, topics_with_index], axis="columns"
        )

        self.only_issues: pd.DataFrame = only_issues
        self.topic_classes: np.ndarray = topic_classes
        self.topics: pd.DataFrame = topics_with_index
        self.only_issues_with_labels: pd.DataFrame = only_issues_with_labels

    def only_topics(self) -> pd.DataFrame:
        """
        Return only the columns in the `only_issues` DataFrame that are topic
        labels.

        Returns a DataFrame of shape (NUM_ISSUES, NUM_TOPIC_LABELS).
        Normally around (15000, 50).

        The row indicies are sort of (but not exactly) issue numbers on GitHub (not 0...15000).
        """
        # TODO: Don't hardcode 14 here, but calculate it from self.only_issues
        return self.only_issues_with_labels.iloc[:, 14:]

    def topic_totals(self) -> pd.Series:
        """
        Return the totals for each topic labels.  This allows you to quickly see
        which topic labels are the most used.

        Returns a `Series` of shape (NUM_TOPIC_LABELS,).
        """
        return self.only_topics().sum().sort_values(0)

    def top_n_topics(self, n=15) -> pd.DataFrame:
        """
        Returns only the top `n` values of `self.topic_totals()`.

        Returns a `Series` of shape (n,).
        """
        return self.topic_totals()[-n:]

class Stage2PreprocData:
    """
    This is the second stage of preprocessing the issue data.

    This takes the Stage1PreprocData and turns it into TensorFlow Datasets that
    we can operate on.
    """

    def __init__(self, stage1: pd.DataFrame = None, input_text_len: int = 1000, top_n_topics: int = 15) -> None:
        self.stage1 = Stage1PreprocData() if stage1 is None else stage1
        self.input_text_len = input_text_len
        self.top_n_topics = top_n_topics

    def process(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Return the input data and labels.

        X is a `DataFrame` of input data with one column for the issue number,
        and then one column that is the username, issue title, and issue body,
        chopped to the first 1000 characters.

        Y is a `DataFrame` of one-hot-encoded topic labels.
        """
        def create_input_text(row: pd.Series) -> pd.Series:
            # print(type(row))
            author = row["user_login"]
            title = row["title"]
            body = row["body"]
            issue_num = row["number"]
            return pd.Series([issue_num, f"{author}\n{title}\n{body}"[:self.input_text_len]], index=["issue_num", "issue_text"])

        X: pd.Series = self.stage1.only_issues.apply(create_input_text, axis=1)
        Y: pd.DataFrame = self.stage1.only_topics()[self.stage1.top_n_topics(self.top_n_topics).index]

        return X, Y

    def to_encoded(self) -> Tuple[pd.Series, np.ndarray, pd.DataFrame]:
        X, Y = self.process()

        issue_body = X.iloc[:, 1]

        num_issues = issue_body.shape[0]

        def to_ascii(c: str) -> int:
            """
            Convert a character to ascii.  Returns 0 for all characters that
            are not ascii.15916
            """
            val = ord(c)
            return 0 if val > 127 else val

        def to_ascii_array(iss_bod: str) -> np.ndarray:
            padded_issue_body = iss_bod.ljust(self.input_text_len, "\0")
            new_array = np.fromiter((to_ascii(c) for c in padded_issue_body), dtype="int8")
            assert len(new_array) == self.input_text_len
            return new_array

        # This is a (NUM_ISSUES * TEXT_LEN,) array of ascii-encoded issue bodies.
        issue_body_ascii: np.ndarray = np.concatenate([to_ascii_array(iss) for iss in issue_body])

        # This is a (NUM_ISSUES, TEXT_LEN) array of ascii-encoded issue bodies.
        # This is normally around (15000, 1000)
        issue_body_ascii_reshaped: np.ndarray = issue_body_ascii.reshape((num_issues, self.input_text_len))

        return X["issue_num"], issue_body_ascii_reshaped, Y

    def to_tf(self) -> tf.data.Dataset:
        issue_nums, issue_body_ascii, Y = self.to_encoded()

        # This is a dataset where each element has three tensors.  The first one
        # is the input ascii issue body.  It is shape (TEXT_LEN,).  It is
        # normally around (1000,).
        #
        # The second tensor is the topic labels we want to predict.  It is
        # shape (NUM_TOP_N_TOPIC_LABELS,).  It is normally around (15,).
        #
        # The third tensor are the issue numbers.  This should be ignored while
        # training.
        dataset = tf.data.Dataset.from_tensor_slices((issue_body_ascii, Y.values, issue_nums))

        # Shuffle the dataset.
        dataset = dataset.shuffle(buffer_size=20000, seed=42, reshuffle_each_iteration=False)

        return dataset

    def to_datasets(self, test_set_size: int = 1500, val_set_size: int = 1600) -> Tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset]:
        """
        Return Datasets containing the training data, the validation data, and
        the testing data.

        These datasets are of shape:

        - ((NUM_TRAIN_ISSUES,), (NUM_TOP_N_TOPIC_LABELS,), ())
        - ((NUM_VAL_ISSUES,), (NUM_TOP_N_TOPIC_LABELS,), ())
        - ((NUM_TEST_ISSUES,), (NUM_TOP_N_TOPIC_LABELS,), ())

        These are normally around the size:

        - ((12000,), (15,), ())
        - ((1600,), (15,), ())
        - ((1500,), (15,), ())

        TODO: These three datasets haven't been stratified (which means that
        the ratio of issue labels in each dataset may be slightly different due
        to randomness).
        """
        dataset = self.to_tf()

        test_set = dataset.take(test_set_size)
        dataset = dataset.skip(test_set_size)

        val_set = dataset.take(val_set_size)
        dataset = dataset.skip(val_set_size)
        train_set = dataset

        return train_set, val_set, test_set

