#!/usr/bin/env python3

import pandas as pd  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore

from issue_tagging_bot.issue_data import issue_data_frame


def main() -> None:
    all_issue_data = issue_data_frame()

    only_issues = all_issue_data[all_issue_data.is_issue]
    issues_series: pd.Series = only_issues.labels.apply(lambda val: set(map(lambda l: l["name"], val)))
    print(issues_series)
    print()

    mlb = MultiLabelBinarizer()
    res = mlb.fit_transform(issues_series)
    print(res)
    print()
    print(mlb.classes_)

    for c in mlb.classes_:
        print(c)

    return


if __name__ == "__main__":
    # execute only if run as a script
    main()
