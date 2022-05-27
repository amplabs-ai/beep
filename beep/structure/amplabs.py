"""Classes and functions for handling AmpLabs cycler data.

"""
import os
from datetime import datetime

import pytz
import pandas as pd
import numpy as np

from beep.structure.base import BEEPDatapath


class AmpLabsDatapath(BEEPDatapath):
    """A datapath for cycler data hosted on AmpLabs.

    AmpLabs OpenAPI provides access to timeseries and cycle series data

    Attributes:
        All from BEEPDatapath
    """

    # Mapping of raw data file columns to BEEP columns
    COLUMN_MAPPING = {
        "test_time (s)": "test_time",
        "cycle_index": "cycle_index",
        "current (a)": "current",
        "voltage (v)": "voltage",
        "charge_capacity (ah)": "charge_capacity",
        "discharge_capacity (ah)": "discharge_capacity",
        "charge_energy (wh)": "charge_energy",
        "discharge_energy (wh)": "discharge_energy",
        "cell_temperature (c)": "temperature",
        "date_time": "date_time"
    }

    # Columns to ignore
    COLUMNS_IGNORE = ["environment_temperature (c)"]

    # Mapping of data types for BEEP columns
    DATA_TYPES = {
        "test_time": "float64",
        "cycle_index": "int32",
        "current": "float32",
        "voltage": "float32",
        "charge_capacity": "float64",
        "discharge_capacity": "float64",
        "charge_energy": "float64",
        "discharge_energy": "float64",
        "temperature": "float32",
        "date_time": "float32",
    }

    FILE_PATTERN = ".*timeseries\\.csv"

    @classmethod
    def from_api(cls):
        # API Logic to fetch public data
        # load data into dataframe
        raise NotImplementedError

    @classmethod
    def from_file(cls, path):
        """Load a AmpLabs cycler file from raw file.

        Args:
            path (str, Pathlike): Path to the raw data csv.

        Returns:
            (AmpLabsDatapath)
        """

        df = pd.read_csv(path)
        return cls.from_df(df)

    @classmethod
    def from_df(cls, df):
        """Load a AmpLabs cycler file from DataFrame.

        Args:
            path (str, DataFrame): DataFrame of raw data.

        Returns:
            (AmpLabsDatapath)
        """

        df.rename(str.lower, axis="columns", inplace=true)
        df.drop(columns=[c for c in cls.columns_ignore if c in df.columns], inplace=true)
        df["step_index"] = df['cycle_index']
        df["step_time"] = df["cycle_time"]

        df.rename(columns=cls.column_mapping, inplace=true)
        dtfmt = '%y-%m-%d %h:%m:%s.%f'
        # convert date time string to
        dts = df["date_time"].apply(lambda x: datetime.strptime(x, dtfmt))

        df["date_time"] = dts.apply(lambda x: x.timestamp())
        df["date_time_iso"] = dts.apply(lambda x: x.replace(tzinfo=pytz.utc).isoformat())

        for column, dtype in cls.data_types.items():
            if column in df:
                if not df[column].isnull().values.any():
                    df[column] = df[column].astype(dtype)

        paths = {
            "raw": os.path.abspath(path),
            "metadata": none
        }

        # there is no metadata given in the ba files
        metadata = {}

        return cls(df, metadata, paths)

