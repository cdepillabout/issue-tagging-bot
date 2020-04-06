#!/usr/bin/env python3

import numpy as np
import pandas as pd  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore

from issue_tagging_bot.issue_data import issue_data_frame

def top_n_topics(n=10, sorted_topic_totals=None):
    if sorted_topic_totals is None:
        sorted_topic_totals = topic_totals()

    return sorted_topic_totals[- n:]

def topic_totals(all_topics=None):
    if all_topics is None:
        all_topics = only_topics()

    return all_topics.sum().sort_values(0)

def top_n_topics(n=10, all_topics=None):
    if all_topics is None:
        all_topics = only_topics()

    return all_topics.sum().sort_values(0)[- n:]

def only_topics(only_issues_with_labels=None):
    if only_issues_with_labels is None:
        only_issues_with_labels = issues_with_topics()

    return only_issues_with_labels.iloc[:, 14:]

def issues_with_topics():
    only_issues, topic_classes, topics = main()
    only_issues_with_labels = pd.concat([only_issues, topics], axis="columns")
    return only_issues_with_labels

def main():
    all_issue_data = issue_data_frame()

    only_issues = all_issue_data[all_issue_data.is_issue]
    label_series: pd.Series = only_issues.labels.apply(lambda val: set(map(lambda l: l["name"], val)))

    mlb = MultiLabelBinarizer()
    res = mlb.fit_transform(label_series)

    topic_label_selector = np.char.startswith(mlb.classes_.astype(str), "6.")
    topic_classes =  mlb.classes_[topic_label_selector]
    topic_labels = res[:, topic_label_selector]
    topics = pd.DataFrame(data=topic_labels, columns=topic_classes)

    only_issues_indicies = only_issues.index
    topics = topics.set_index(only_issues_indicies)

    return only_issues, topic_classes, topics


if __name__ == "__main__":
    # execute only if run as a script
    main()
