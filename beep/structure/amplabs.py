"""Classes and functions for handling AmpLabs cycler data.

"""
import os
import urllib
import json
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
        "Test_Time (s)": "test_time",
        "Cycle_Index": "cycle_index",
        "Current (a)": "current",
        "Voltage (v)": "voltage",
        "Charge_Capacity (ah)": "charge_capacity",
        "Discharge_Capacity (ah)": "discharge_capacity",
        "Charge_Energy (wh)": "charge_energy",
        "Discharge_Energy (wh)": "discharge_energy",
        "Cell_Temperature (c)": "temperature"
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
    @classmethod
    def from_amplabs(cls, dataset):
        df = AmpLabsDatapath.get_amplabs_dataset(dataset)
        return AmpLabsDatapath.from_df(df)

    @classmethod
    def get_amplabs_dataset(cls, dataset):
        url = "https://www.amplabs.ai/download/cells/cycle_timeseries_json?cell_id={}".format(dataset)
        user = "public@amplabs.ai"
        httprequest = urllib.request.Request(
            url, method="GET"
        )
        httprequest.add_header("Cookie", f"userId={user}")

        try:
            with urllib.request.urlopen(httprequest) as httpresponse:
                response = json.loads(httpresponse.read())
                return pd.DataFrame(response['records'])
        except urllib.error.HTTPError as e:
            print(e)
        return None

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

        df.rename(columns=cls.COLUMN_MAPPING, inplace=True)
        df.rename(str.lower, axis="columns", inplace=True)
        df.drop(columns=[c for c in cls.COLUMNS_IGNORE if c in df.columns], inplace=True)
        df["step_index"] = df['cycle_index']
        df["step_time"] = df['test_time'] # Need to update with cycle_time
        dtfmt = '%Y-%m-%dT%H:%M:%S.%fZ'
        dts = df["date_time"].apply(lambda x: datetime.strptime(x, dtfmt))
        df["date_time"] = dts.apply(lambda x: x.timestamp())
        df["date_time_iso"] = dts.apply(lambda x: x.isoformat())

        for column, dtype in cls.DATA_TYPES.items():
            if column in df:
                if not df[column].isnull().values.any():
                    df[column] = df[column].astype(dtype)

        paths = {
            "raw": None,
            "metadata": None
        }
        # there is no metadata given in the ba files
        metadata = {}

        return cls(df, metadata, paths)

