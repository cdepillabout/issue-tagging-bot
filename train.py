#!/usr/bin/env python3

import tensorflow as tf

from issue_tagging_bot.issue_data import Stage1PreprocData, Stage2PreprocData

def only_python_labels(dataset: tf.data.Dataset) -> tf.data.Dataset:
    dataset.map

def main() -> None:

    stage2 = Stage2PreprocData()
    train_set, val_set, test_set = stage2.to_datasets()

    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(300, input_shape=[1000], activation="relu"),
        tf.keras.layers.Dense(15, activation="sigmoid")
    ])

    model.summary()


if __name__ == "__main__":
    main()
