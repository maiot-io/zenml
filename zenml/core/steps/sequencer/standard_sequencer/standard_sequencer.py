#  Copyright (c) maiot GmbH 2021. All Rights Reserved.
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

from typing import Dict, Text

import apache_beam as beam
import dateutil
import pandas as pd
import pytz
from apache_beam.transforms.window import Sessions
from apache_beam.transforms.window import TimestampedValue
from apache_beam.utils.timestamp import Timestamp
from tensorflow_transform.tf_metadata import schema_utils

from zenml.core.steps.sequencer.base_sequencer import BaseSequencerStep
from zenml.core.steps.sequencer.standard_sequencer import utils
from zenml.core.steps.sequencer.standard_sequencer.methods \
    .standard_methods import ResamplingMethods, FillingMethods
from zenml.utils.preprocessing_utils import parse_methods, DEFAULT_DICT


class StandardSequencer(BaseSequencerStep):

    def __init__(self,
                 timestamp_column: Text,
                 category_column: Text = None,
                 overwrite: Dict[Text, Text] = None,
                 resampling_rate: int = 1000,
                 gap_threshold: int = 60000,
                 sequence_length: int = 16,
                 sequence_shift: int = 1,
                 **kwargs):

        self.timestamp_column = timestamp_column
        self.category_column = category_column
        self.overwrite = overwrite
        self.sequence_length = sequence_length
        self.sequence_shift = sequence_shift
        self.resampling_rate = resampling_rate
        self.gap_threshold = gap_threshold

        self.resampling_dict = parse_methods(overwrite or {},
                                             'resampling',
                                             ResamplingMethods)

        self.resampling_default_dict = parse_methods(DEFAULT_DICT,
                                                     'resampling',
                                                     ResamplingMethods)

        self.filling_dict = parse_methods(overwrite or {},
                                          'filling',
                                          FillingMethods)

        self.filling_default_dict = parse_methods(DEFAULT_DICT,
                                                  'filling',
                                                  FillingMethods)

        super(StandardSequencer, self).__init__(
            timestamp_column=timestamp_column,
            category_column=category_column,
            overwrite=overwrite,
            resampling_rate=resampling_rate,
            gap_threshold=gap_threshold,
            sequence_length=sequence_length,
            sequence_shift=sequence_shift,
            **kwargs)

    def get_category_do_fn(self):
        default_category = '__default__'
        category_column = self.category_column

        class AddKey(beam.DoFn):
            def process(self, element):
                """
                Add the category as a key to each element
                """
                if category_column:
                    element = element.set_index(
                        element[category_column].apply(
                            lambda x: x[0].decode('utf-8')),
                        drop=False)
                else:
                    element[default_category] = default_category
                    element = element.set_index(default_category)
                return element.iterrows()

        return AddKey

    def get_timestamp_do_fn(self):

        timestamp_column = self.timestamp_column

        class AddTimestamp(beam.DoFn):
            def process(self, element):
                """
                Parse the timestamp and add it to the datapoints
                """
                timestamp = dateutil.parser.parse(element[timestamp_column][0])
                timestamp_utc = timestamp.astimezone(pytz.utc)
                unix_timestamp = Timestamp.from_utc_datetime(timestamp_utc)
                yield TimestampedValue(element, unix_timestamp)

        return AddTimestamp

    def get_window(self):
        return Sessions(self.gap_threshold)

    def get_combine_fn(self):
        epoch_suffix = '_epoch'

        timestamp_column = self.timestamp_column
        category_column = self.category_column
        overwrite = self.overwrite
        sequence_length = self.sequence_length
        sequence_shift = self.sequence_shift
        resampling_rate = self.resampling_rate
        gap_threshold = self.gap_threshold
        resampling_dict = self.resampling_dict
        resampling_default_dict = self.resampling_default_dict
        filling_dict = self.filling_dict
        filling_default_dict = self.filling_default_dict

        class SequenceCombine(beam.CombineFn):
            def create_accumulator(self, *args, **kwargs):
                return pd.DataFrame()

            def add_input(self, mutable_accumulator, element, *args, **kwargs):
                return mutable_accumulator.append(element)

            def merge_accumulators(self, accumulators, *args, **kwargs):
                return pd.concat(accumulators)

            def extract_output(self, accumulator, *args, **kwargs):
                # Get the required args
                config_dict = args[0]
                s = schema_utils.schema_as_feature_spec(args[1]).feature_spec
                schema = utils.infer_schema(s)

                # Extract the values from the arrays within the cells
                session = accumulator.applymap(utils.array_to_value)

                # Extract the category if there is one
                cat = None
                if category_column:
                    cat = session[category_column].unique()[0].decode('utf-8')

                # Set the timestamp as the index
                session[timestamp_column] = session[timestamp_column].apply(
                    lambda x: pd.to_datetime(x.decode('utf-8')))
                session = session.set_index(timestamp_column)

                # RESAMPLING
                r_config = utils.fill_defaults(resampling_dict,
                                               resampling_default_dict,
                                               schema)

                resample_functions = utils.get_function_dict(
                    r_config, ResamplingMethods)

                for key, function_list in resample_functions.items():
                    assert len(function_list) == 1, \
                        'Please only define a single function for resampling'
                    resample_functions[key] = function_list[0]

                feature_list = list(resample_functions.keys())
                for feature in feature_list:
                    if feature not in session:
                        session[feature] = None

                resampler = session[feature_list].resample(
                    '{}L'.format(resampling_rate))

                session = resampler.agg(resample_functions)

                # TODO: Investigate the outcome of disabling this
                # session = session.dropna(subset=config_dict[cts.FEATURES],
                #                          how='all',
                #                          axis=0)

                # Resolving the dtype conflicts after resampling
                output_dt_map = utils.get_resample_output_dtype(
                    resampling_dict,
                    schema)
                session = session.astype(output_dt_map)

                # FILLING
                f_config = utils.fill_defaults(filling_dict,
                                               filling_default_dict,
                                               schema)

                filling_functions = utils.get_function_dict(f_config,
                                                            FillingMethods)

                for key, function_list in filling_functions.items():
                    assert len(function_list) == 1, \
                        'Please only define a single function for filling'
                    filling_functions[key] = function_list[0]
                session = session.agg(filling_functions)

                # Required Keys
                if category_column:
                    session[category_column] = cat

                index_s = session.index.to_series(keep_tz=True)
                session[timestamp_column] = index_s.apply(
                    lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f %Z"))

                session[timestamp_column + epoch_suffix] = index_s.apply(
                    lambda x: utils.convert_datetime_to_secs(x))

                session.sort_index(inplace=True)

                return utils.extract_sequences(session,
                                               sequence_length,
                                               resampling_rate,
                                               sequence_shift)

        return SequenceCombine