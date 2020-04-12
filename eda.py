#!/usr/bin/env python3

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore

from issue_tagging_bot.issue_data import IssueFiles

def top_n_topics(n=10, sorted_topic_totals=None):
    if sorted_topic_totals is None:
        sorted_topic_totals = topic_totals()

    return sorted_topic_totals[- n:]

def topic_totals(all_topics=None):
    if all_topics is None:
        all_topics = only_topics()

    return all_topics.sum().sort_values(0)

def only_topics(only_issues_with_labels=None):
    if only_issues_with_labels is None:
        only_issues_with_labels = issues_with_topics()

    return only_issues_with_labels.iloc[:, 14:]

def issues_with_topics():
    only_issues, topic_classes, topics = main()
    only_issues_with_labels = pd.concat([only_issues, topics], axis="columns")
    return only_issues_with_labels

def main():
    issue_files = IssueFiles()

    # Get a single dataframe with only issues data.
    only_issues: pd.DataFrame = issue_files.issues_data_frame()

    # Create a series that has the labels on each issue.  This returns a Series
    # that is NUM_LABELS long (normally around 100 labels).
    label_series: pd.Series = only_issues.labels.apply(lambda val: set(map(lambda l: l["name"], val)))

    mlb: MultiLabelBinarizer = MultiLabelBinarizer()

    # This is a one-hot-encoded numpy array with ones for each label.  This is
    # of size (NUM_ISSUES, NUM_LABELS).  Normally around (15000, 100).
    res: np.ndarray = mlb.fit_transform(label_series)

    # This is a boolean array with True for each label that starts with "6.".
    # These are the topic labels we want to be able to predict, like "Haskell",
    # "QT", "Rust", etc.  This is of shape (NUM_LABELS,).
    topic_label_selector: np.ndarray = np.char.startswith(mlb.classes_.astype(str), "6.")

    # This is a string array that contains only the labels that start with
    # "6.".  This is of shape (NUM_TOPIC_LABELS,).  Normally around (50,).
    topic_classes: np.ndarray =  mlb.classes_[topic_label_selector]

    # This is a one-hot array with a 1 for each issue that has a given
    # topic-label.  This is of shape (NUM_ISSUES, NUM_TOPIC_LABELS).  Normally
    # around (15000, 50).
    topic_labels: np.ndarray = res[:, topic_label_selector]

    # A DataFrame where the rows are all an index from 0 to NUM_ISSUES, and the columns are
    # topic labels.  This is of shape (NUM_ISSUES, NUM_TOPIC_LABELS).  Normally
    # around (15000, 50).
    topics: pd.DataFrame = pd.DataFrame(data=topic_labels, columns=topic_classes)

    # A list of indicies of only the issues.
    only_issues_indicies: pd.core.indexes.numeric.Int64Index = only_issues.index

    # This is the same as topics above, but the indicies are the indicies of
    # the actual issues on GitHub (not 0 to NUM_ISSUES).
    topics: pd.DataFrame = topics.set_index(only_issues_indicies)

    return only_issues, topic_classes, topics


if __name__ == "__main__":
    # execute only if run as a script
    main()
