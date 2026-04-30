import numpy as np
from sklearn.neural_network import MLPClassifier
import tensorflow as tf
import tensorflow_datasets as tfds


def train_dnn():
    (ds_train, ds_test), ds_info = tfds.load(
        'mnist',
        split=['train', 'test'],
        as_supervised=True,
        with_info=True,
    )

    def normalize_img(image, label):
        return tf.cast(tf.reshape(image, (28*28,)), tf.float32) / 255., label

    ds_train = ds_train.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
    ds_train = ds_train.cache()
    ds_train = ds_train.batch(128)
    ds_train = ds_train.prefetch(tf.data.AUTOTUNE)

    ds_test = ds_test.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
    ds_test = ds_test.batch(128)
    ds_test = ds_test.cache()
    ds_test = ds_test.prefetch(tf.data.AUTOTUNE)
    
    X_train, y_train = [], []
    for x, y in tfds.as_numpy(ds_train):
        X_train.append(x)
        y_train.append(y)
    X_train = np.concatenate(X_train, axis=0)
    y_train = np.concatenate(y_train)

    X_test, y_test = [], []
    for x, y in tfds.as_numpy(ds_test):
        X_test.append(x)
        y_test.append(y)
    X_test = np.concatenate(X_test, axis=0)
    y_test = np.concatenate(y_test)

    model = MLPClassifier(hidden_layer_sizes=(128), max_iter=10, verbose=True).fit(X_train, y_train)
    print(model.score(X_test, y_test))

    return model, (X_train, y_train), (X_test, y_test)
