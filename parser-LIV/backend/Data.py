from typing import List, Tuple
from math import nan

import re


class Data:
    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.lines: List[str] = None

        # LIV data
        self.LIV_section_markers: List[str] = [
            "### LIV Data ###",
            "### Spectrum LIV Data ###"
        ]
        self.LIV_section_parse_length: int = 7
        self.LIV_row_markers: List[str] = [
            "Set, A",
            "AI_Voltage",
            "AI_Current",
            "OPM",
            "Power, W",
            "Voltage, V",
            "Current, A",
            "WLmean, nm",
        ]
        
        self.LIV: dict[str, List[float]] = {}

        # Additional to LIV data
        self.additional_data_names: List[str] = [
            "Duration, us",
            "Frequency, Hz"
        ]
        self.additional_data_patterns: List[str] = [
            r"Duration:\s*([0-9]*\.?[0-9]+)us",
            r"Frequency:\s*([0-9]*\.?[0-9]+)Hz"
        ]
        self.additional_data_values: List[str] = [None] \
            * len(self.additional_data_names)

        self.naming_data_name: str = ""
        self.naming_data_value: str = ""

        self.number_pattern = r'[-+]?\d*\.?\d+|NaN|nan|NAN'

        return

    @property
    def is_invalid(self):
        return (len(self.LIV) < 2)

    def read_lines_from_file(self) -> None:
        with open(self.filepath, "r", errors="ignore") as file:
            self.lines = file.readlines()
        return
    
    def parse_LIV_row(self, string, varname_pattern):
        varname_match = re.match(varname_pattern, string)
        if not varname_match:
            return
        varname = varname_match.group()
        number_matches = re.findall(self.number_pattern, string[len(varname):])
        numbers = []
        for match in number_matches:
            try:
                float_match = float(match)
                numbers.append(float_match)
            except ValueError:
                numbers.append(nan)

        return varname, numbers

    def match_line_with_pattern(self, pattern: str) -> str:
        for line in self.lines:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return

    def add_nameing(self, value: str) -> None:
        self.naming_data_name = "Name"
        self.naming_data_value = str(value)
        return

    def get_naming(self) -> Tuple[str, str]:
        return (self.naming_data_name, self.naming_data_value)

    def parse(self) -> None:
        self.parse_additional_data()
        self.parse_LIV()
        return

    def parse_additional_data(self) -> None:
        for (i, pattern) in enumerate(self.additional_data_patterns):
            value: str = self.match_line_with_pattern(pattern)

            # Try to change Duration from "us" to "ms"
            if i == 0:  # "Duration, us"
                try:
                    value = str(round(float(value)/1000, ndigits=2))
                    self.additional_data_names[i] = "Duration, ms"
                except:
                    pass

            self.additional_data_values[i] = value
        return

    def parse_LIV(self) -> None:
        section_is = []
        for section_marker in self.LIV_section_markers:
            for (i, line) in enumerate(self.lines):
                if section_marker in line:
                    section_is.append(i)

        if not section_is:
            return
        
        for section_i in section_is:
            for i in range(section_i, section_i+self.LIV_section_parse_length):
                line = self.lines[i]
                prev_line = self.lines[i-1]
                for marker in self.LIV_row_markers:
                    
                    name_values = self.parse_LIV_row(line, marker)
                    if not name_values:
                        continue
                    name, values = name_values
                    if marker == "WLmean, nm":
                        DAT = re.findall(self.number_pattern, prev_line)[0]
                        if DAT:
                            name += f" (DAT={DAT}ms)"
                    self.LIV[name] = values
        return
