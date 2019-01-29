import numpy as np
import tensorflow as tf


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _float_list_feature(value):
    data = _bytes_feature(
        tf.compat.as_bytes(np.array(value, dtype=np.float32).tostring()))

    return data


class DataRecord:

    def __init__(self, tfrecord_path=""):
        self.tfrecord_path = tfrecord_path
        self.keys = ['timestamp', 'ask_price', 'ask_qty',
                     'bid_price', 'bid_qty']

    def open(self, tfrecord_path=""):
        if tfrecord_path != "":
            self.tfrecord_path = tfrecord_path

        self.writer = tf.python_io.TFRecordWriter(
            path=self.tfrecord_path)

    def close(self):
        self.writer.close()

    def write(self, data):
        example = tf.train.Example(
            features=tf.train.Features(
                feature={
                    self.keys[0]: _int64_feature(
                        data[self.keys[0]]),
                    self.keys[1]: _float_list_feature(
                        data[self.keys[1]]),
                    self.keys[2]: _float_list_feature(
                        data[self.keys[2]]),
                    self.keys[3]: _float_list_feature(
                        data[self.keys[3]]),
                    self.keys[4]: _float_list_feature(
                        data[self.keys[4]]),
                }
            )
        )

        self.writer.write(example.SerializeToString())

    def decode(self, string_record):
        example = tf.train.Example()
        example.ParseFromString(string_record)

        data = dict()
        for key in self.keys[1:]:
            data_string = (example.features.feature[key].bytes_list.value[0])
            data[key] = np.fromstring(data_string, dtype=np.float32)

        data[self.keys[0]] = \
            example.features.feature[self.keys[0]].int64_list.value[0]

        return data
