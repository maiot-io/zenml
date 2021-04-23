#  Copyright (c) maiot GmbH 2020. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""TFDS Datasource definition"""

from typing import Text, Callable

import tensorflow_datasets as tfds

from zenml.datasources import BaseDatasource


class TFDSDatasource(BaseDatasource):
    """ZenML TFDS datasource definition."""

    def __init__(
            self,
            name: Text,
            tfds_dataset_name: Text,
            shuffle_files: bool = False,
            as_supervised: bool = False,
            with_info: bool = False,
            **kwargs):
        """
        ZenML TFDS wrapper.

        Args:
            name:
            tfds_dataset_name:
            shuffle_files:
            as_supervised:
            with_info:
            **kwargs:
        """
        self.name = name
        self.tfds_dataset_name = tfds_dataset_name
        self.shuffle_files = shuffle_files
        self.as_supervised = as_supervised
        self.with_info = with_info
        super().__init__(
            name,
            tfds_dataset_name=tfds_dataset_name,
            shuffle_files=shuffle_files,
            as_supervised=as_supervised,
            with_info=with_info,
            **kwargs)

    def process(self, output_path: Text, make_beam_pipeline: Callable = None):
        tfds.load(
            self.tfds_dataset_name,
            download=True,
            data_dir=output_path,
            shuffle_files=self.shuffle_files,
            as_supervised=self.as_supervised,
            with_info=self.with_info,
        )