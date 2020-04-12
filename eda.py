#!/usr/bin/env python3

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
from sklearn.preprocessing import MultiLabelBinarizer  # type: ignore

from issue_tagging_bot.issue_data import IssueFiles

def main() -> None:
    stage_1_preproc = Stage1PreprocData()

if __name__ == "__main__":
    # execute only if run as a script
    main()
