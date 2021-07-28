# Copyright [2020] [Toyota Research Institute]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for maccor protcol files to biologic modulo bat protcol files"""

import os
import unittest
import xmltodict
from collections import OrderedDict
from monty.tempfile import ScratchDir

from beep.protocol import (
    PROTOCOL_SCHEMA_DIR,
    BIOLOGIC_TEMPLATE_DIR,
    PROCEDURE_TEMPLATE_DIR,
)
from beep.protocol.maccor_to_biologic_mb import MaccorToBiologicMb, CycleAdvancementRules, CycleAdvancementRulesSerializer

TEST_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(TEST_DIR, "test_files")


class ConversionTest(unittest.TestCase):
    maxDiff = None

    def maccor_values_to_biologic_value_and_unit_test(self, func, tests):
        for value_str, expected_value_str, expected_unit in tests:
            actual_value, actual_unit = func(value_str)            
            self.assertEqual(actual_value, expected_value_str)
            self.assertEqual(actual_unit, expected_unit)

    def test_convert_volts(self):
        converter = MaccorToBiologicMb()
        tests = [
            ("0.1429", "142.900", "mV"),
            ("0.1429e3", "142.900", "V"),
            ("159.3624", "159362.400", "mV"),
            ("152.9", "152.900",  "V")
        ]
        self.maccor_values_to_biologic_value_and_unit_test(
            converter._convert_volts,
            tests,
        )
    
    def test_convert_amps(self):
        converter = MaccorToBiologicMb()
        tests = [
            ("0.1429", "142.900", "mA"),
            ("1.23", "1.230", "A"),
            ("152.9", "152.900",  "A"),
            ("1.2e-4", "120.000", "\N{Micro Sign}A")
        ]
        self.maccor_values_to_biologic_value_and_unit_test(
            converter._convert_amps,
            tests,
        )

    def test_convert_watts(self):
        converter = MaccorToBiologicMb()
        tests = [
            ("0.1429", "142.900", "mW"),
            ("1.23", "1.230", "W"),
            ("152.9", "152.900",  "W"),
            ("1.2e-5", "12.000", "\N{Micro Sign}W")
        ]
        self.maccor_values_to_biologic_value_and_unit_test(
            converter._convert_watts,
            tests,
        )

    def test_convert_ohms(self):
        converter = MaccorToBiologicMb()
        tests = [
            ("0.1429", "142.900", "mOhms"),
            ("1.459e4", "14.590", "kOhms"),
            ("152.9", "152.900",  "Ohms"),
            ("1.2e-4", "120.000", "\N{Micro Sign}Ohms")
        ]
        self.maccor_values_to_biologic_value_and_unit_test(
            converter._convert_ohms,
            tests,
        )
    
    def test_convert_time(self):
        converter = MaccorToBiologicMb()
        tests = [
            ("::.01", "10.000", "ms"),
            ("03::", "3.000", "h"),
            ("03:30:", "210.000",  "mn"),
            ("00:00:50", "50.000", "s")
        ]
        self.maccor_values_to_biologic_value_and_unit_test(
            converter._convert_time,
            tests,
        )

        def single_step_to_single_seq_test(self, test_step_xml, diff_dict):
        """
        test utility for testing proc_step_to_seq
         """
        proc = xmltodict.parse(test_step_xml)
        test_step = proc["MaccorTestProcedure"]["ProcSteps"]["TestStep"]
        converter = MaccorToBiologicMb()

        expected = converter._blank_seq.copy()
        expected["Ns"] = 0
        expected["lim1_seq"] = 1
        expected["lim2_seq"] = 1
        expected["lim3_seq"] = 1
        expected.update(diff_dict)

        step_num = 1
        seq_nums_by_step_num = {
            step_num: [0],
            step_num + 1: [1],
        }

        result = converter._convert_step_parts(
            step_parts=[test_step],
            step_num=step_num,
            seq_nums_by_step_num=seq_nums_by_step_num,
            goto_lowerbound=0,
            goto_upperbound=3,
            end_step_num=4,
        )[0]

        for key, value in expected.items():
            self.assertEqual(
                value,
                result[key],
                msg="Expected {0}: {1} got {0}: {2}".format(key, value, result[key]),
            )

    def test_rest_step_conversion(self):
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<MaccorTestProcedure>"
            "  <ProcSteps>"
            "    <TestStep>"
            "      <StepType>  Rest  </StepType>"
            "      <StepMode>        </StepMode>"
            "      <StepValue></StepValue>"
            "      <Limits/>"
            "      <Ends>"
            "        <EndEntry>"
            "          <EndType>Voltage </EndType>"
            "          <SpecialType> </SpecialType>"
            "          <Oper>&gt;= </Oper>"
            "          <Step>002</Step>"
            "          <Value>4.4</Value>"
            "        </EndEntry>"
            "        <EndEntry>"
            "          <EndType>Voltage </EndType>"
            "          <SpecialType> </SpecialType>"
            "          <Oper>&lt;= </Oper>"
            "          <Step>002</Step>"
            "          <Value>2.5</Value>"
            "        </EndEntry>"
            "      </Ends>"
            "      <Reports>"
            "        <ReportEntry>"
            "          <ReportType>Voltage</ReportType>"
            "          <Value>2.2</Value>"
            "        </ReportEntry>"
            "      </Reports>"
            "      <Range>A</Range>"
            "      <Option1>N</Option1>"
            "      <Option2>N</Option2>"
            "      <Option3>N</Option3>"
            "      <StepNote></StepNote>"
            "    </TestStep>"
            "  </ProcSteps>"
            "</MaccorTestProcedure>"
        )
        diff_dict = {
            "ctrl_type": "Rest",
            "Apply I/C": "I",
            "N": "1.00",
            "charge/discharge": "Charge",
            "lim_nb": 2,
            "lim1_type": "Ecell",
            "lim1_comp": ">",
            "lim1_value": "4.400",
            "lim1_value_unit": "V",
            "lim2_type": "Ecell",
            "lim2_comp": "<",
            "lim2_value": "2.500",
            "lim2_value_unit": "V",
            "rec_nb": 1,
            "rec1_type": "Ecell",
            "rec1_value": "2.200",
            "rec1_value_unit": "V",
        }

        self.single_step_to_single_seq_test(xml, diff_dict)
        pass

    def test_discharge_current_step_conversion(self):
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<MaccorTestProcedure>"
            "  <ProcSteps>"
            "    <TestStep>"
            #      mispelling taken directly from sample file
            "      <StepType>Dischrge</StepType>"
            "      <StepMode>Current </StepMode>"
            "      <StepValue>1.0</StepValue>"
            "      <Limits/>"
            "      <Ends>"
            "        <EndEntry>"
            "          <EndType>StepTime</EndType>"
            "          <SpecialType> </SpecialType>"
            "          <Oper> = </Oper>"
            "          <Step>002</Step>"
            "          <Value>00:00:30</Value>"
            "        </EndEntry>"
            "        <EndEntry>"
            "          <EndType>Voltage </EndType>"
            "          <SpecialType> </SpecialType>"
            "          <Oper>&lt;= </Oper>"
            "          <Step>002</Step>"
            "          <Value>2.7</Value>"
            "        </EndEntry>"
            "        <EndEntry>"
            "          <EndType>Voltage </EndType>"
            "          <SpecialType> </SpecialType>"
            "          <Oper>&gt;= </Oper>"
            "          <Step>002</Step>"
            "          <Value>4.4</Value>"
            "        </EndEntry>"
            "      </Ends>"
            "      <Reports>"
            "        <ReportEntry>"
            "          <ReportType>Voltage </ReportType>"
            "          <Value>0.001</Value>"
            "        </ReportEntry>"
            "        <ReportEntry>"
            "          <ReportType>StepTime</ReportType>"
            #          10ms
            "          <Value>::.01</Value>"
            "        </ReportEntry>"
            "      </Reports>"
            "      <Range>A</Range>"
            "      <Option1>N</Option1>"
            "      <Option2>N</Option2>"
            "      <Option3>N</Option3>"
            "      <StepNote></StepNote>"
            "    </TestStep>"
            "  </ProcSteps>"
            "</MaccorTestProcedure>"
        )
        diff_dict = {
            "ctrl_type": "CC",
            "Apply I/C": "I",
            "ctrl1_val": "1.000",
            "ctrl1_val_unit": "A",
            "ctrl1_val_vs": "<None>",
            "N": "15.00",
            "charge/discharge": "Discharge",
            "lim_nb": 3,
            "lim1_type": "Time",
            "lim1_comp": ">",
            "lim1_value": "30.000",
            "lim1_value_unit": "s",
            "lim2_type": "Ecell",
            "lim2_comp": "<",
            "lim2_value": "2.700",
            "lim2_value_unit": "V",
            "lim3_type": "Ecell",
            "lim3_comp": ">",
            "lim3_value": "4.400",
            "lim3_value_unit": "V",
            "rec_nb": 2,
            "rec1_type": "Ecell",
            "rec1_value": "1.000",
            "rec1_value_unit": "mV",
            "rec2_type": "Time",
            "rec2_value": "10.000",
            "rec2_value_unit": "ms",
        }

        self.single_step_to_single_seq_test(xml, diff_dict)
        pass

    def test_cycle_transition_serialization(self):
        cycle_transition_rules = CycleAdvancementRules(
            tech_num=2,
            tech_does_loop=True,
            adv_cycle_on_start = 1,
            adv_cycle_on_tech_loop = 1,
            adv_cycle_seq_transitions = {(2, 5): 1, (14, 17): 1},
            debug_adv_cycle_on_step_transitions = {(72, 71): 1, (72, 75): 1},
        )

        serializer = CycleAdvancementRulesSerializer()
        json_str = serializer.json(cycle_transition_rules)
        parsed_cycle_transition_rules = serializer.parse_json(json_str)

        self.assertEqual(
            cycle_transition_rules.__repr__(),
            parsed_cycle_transition_rules.__repr__(),
        )

step_with_bounds_template = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    "<TestStep>\n"
    #  mispelling taken directly from sample file
    "  <StepType>Dischrge</StepType>\n"
    "  <StepMode>Current </StepMode>\n"
    "  <StepValue>1.0</StepValue>\n"
    "  <Limits/>\n"
    "  <Ends>\n"
    "    <EndEntry>\n"
    "      <EndType>Voltage </EndType>\n"
    "      <SpecialType> </SpecialType>\n"
    "      <Oper>&lt;= </Oper>\n"
    "      <Step>002</Step>\n"
    "      <Value>{voltage_v_lowerbound}</Value>\n"
    "    </EndEntry>\n"
    "    <EndEntry>\n"
    "      <EndType>Voltage </EndType>\n"
    "      <SpecialType> </SpecialType>\n"
    "      <Oper>&gt;= </Oper>\n"
    "      <Step>002</Step>\n"
    "      <Value>{voltage_v_upperbound}</Value>\n"
    "    </EndEntry>\n"
    "    <EndEntry>\n"
    "      <EndType>Current </EndType>\n"
    "      <SpecialType> </SpecialType>\n"
    "      <Oper>&lt;= </Oper>\n"
    "      <Step>002</Step>\n"
    "      <Value>{current_a_lowerbound}</Value>\n"
    "    </EndEntry>\n"
    "    <EndEntry>\n"
    "      <EndType>Current </EndType>\n"
    "      <SpecialType> </SpecialType>\n"
    "      <Oper>&gt;= </Oper>\n"
    "      <Step>002</Step>\n"
    "      <Value>{current_a_upperbound}</Value>\n"
    "    </EndEntry>\n"
    "  </Ends>\n"
    "  <Reports></Reports>\n"
    "  <Range>A</Range>\n"
    "  <Option1>N</Option1>\n"
    "  <Option2>N</Option2>\n"
    "  <Option3>N</Option3>\n"
    "  <StepNote></StepNote>\n"
    "</TestStep>\n"
)