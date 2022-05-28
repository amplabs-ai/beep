import unittest
from beep.structure.amplabs import AmpLabsDatapath
from beep.structure.base import BEEPDatapath

class TestAmpLabs(unittest.TestCase):
    def setUp(self) -> None:
        self.output_dir = None
        self.status_json_path = None
        self.input_paths = []

    def test_fetch_data_df(self):
        cell_id = 'SNL_18650_LFP_15C_0-100_0.5/1C_a'
        df = AmpLabsDatapath.get_amplabs_dataset(cell_id)
        print(df.head())
        print(df.columns)
        assert(df.shape == (465885,11))

    def test_parse_df(self):
        cell_id = 'SNL_18650_LFP_15C_0-100_0.5/1C_a'
        df = AmpLabsDatapath.get_amplabs_dataset(cell_id)
        aldp = AmpLabsDatapath.from_df(df)
        assert isinstance(aldp, BEEPDatapath)
        assert isinstance(aldp,AmpLabsDatapath)
