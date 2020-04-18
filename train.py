#!/usr/bin/env python3

import tensorflow as tf

from issue_tagging_bot.issue_data import Stage1PreprocData, Stage2PreprocData

def only_nixos_labels(dataset: tf.data.Dataset) -> tf.data.Dataset:
    return dataset.map(lambda issue_body, labels, issue_num: (issue_body, labels[-1], issue_num))

def main() -> None:

    stage2 = Stage2PreprocData()
    train_set, val_set, test_set = stage2.to_datasets()

    train_set = train_set.shuffle(buffer_size=100000, seed=42, reshuffle_each_iteration=True)

    train_set = only_nixos_labels(train_set)
    val_set = only_nixos_labels(val_set)
    test_set = only_nixos_labels(test_set)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(300, input_shape=[1000], activation="relu"),
        tf.keras.layers.Dense(1, activation="softmax")
    ])

    model.summary()

    model.compile(loss="sparse_categorical_crossentropy", optimizer="sgd", metrics=["accuracy"])

    history = model.fit(train_set, epochs=10, validation_data = val_set)


if __name__ == "__main__":
    main()
