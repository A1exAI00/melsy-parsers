from typing import List, Tuple, Dict
from math import nan

import re

NUMBER_PATTERN = r"[-+]?\d*\.?\d+|NaN|nan|NAN"


class LIVdata:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

        self.lines: List[str] = []
        self.LIV: Dict[str, List[float | str]] = {}
        self.other_data: Dict = {}
        return

    def add_lines(self, lines: List[str]) -> None:
        self.lines = lines
        return

    def add_LIV(self, name: str, values: List[float]) -> None:
        # TODO check if name is in keys already
        self.LIV[name] = values
        return

    def add_other_data(self, name: str, value) -> None:
        self.other_data[name] = value
        return


class LIVparser:
    def __init__(self) -> None:
        return

    def get_lines(self, data: LIVdata) -> None:
        lines = []
        with open(data.filepath, "r", errors="ignore") as file:
            lines = file.readlines()
        data.lines = lines
        return

    def parse(self, filepath: str) -> LIVdata:
        data = LIVdata(filepath)
        self.get_lines(data)
        self.parse_LIV(data)
        self.parse_other_data(data)
        return data

    def parse_LIV(self, data: LIVdata) -> None:
        LIV_section_markers: List[str] = [
            "### LIV Data ###",
            "### Spectrum LIV Data ###",
        ]

        section_is = []
        for section_marker in LIV_section_markers:
            for i, line in enumerate(data.lines):
                if section_marker in line:
                    section_is.append(i)

        if not section_is:
            return

        LIV_row_markers: List[str] = [
            "Set, A",
            "AI_Voltage",
            "AI_Current",
            "OPM",
            "Power, W",
            "Voltage, V",
            "Current, A",
            "WLmean, nm",
        ]

        for section_i in section_is:
            for i in range(section_i, section_i + 7):
                line = data.lines[i]
                prev_line = data.lines[i - 1]
                for marker in LIV_row_markers:

                    name_values = self.parse_LIV_row(line, marker)
                    if not name_values:
                        continue
                    name, values = name_values
                    if marker == "WLmean, nm":
                        DAT = re.findall(NUMBER_PATTERN, prev_line)[0]
                        if DAT:
                            name += f" (DAT={DAT}ms)"
                    data.add_LIV(name, values)
        return

    def parse_LIV_row(self, string, varname_pattern):
        varname_match = re.match(varname_pattern, string)
        if not varname_match:
            return
        varname = varname_match.group()
        number_matches = re.findall(NUMBER_PATTERN, string[len(varname) :])
        numbers = []
        for match in number_matches:
            try:
                float_match = float(match)
                numbers.append(float_match)
            except ValueError:
                numbers.append(nan)

        return varname, numbers

    def match_line_with_pattern(self, data: LIVdata, pattern: str) -> str:
        for line in data.lines:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return

    def parse_other_data(self, data: LIVdata) -> None:
        other_data_patterns: List[str] = [
            r"Duration:\s*([0-9]*\.?[0-9]+)us",
            r"Frequency:\s*([0-9]*\.?[0-9]+)Hz",
        ]
        other_data_names: List[str] = ["Duration, us", "Frequency, Hz"]
        for i, pattern in enumerate(other_data_patterns):
            value: str = self.match_line_with_pattern(data, pattern)

            if i == 0:  # "Duration, us"
                value = str(round(float(value) / 1000, ndigits=2))
                data.add_other_data("Duration, ms", value)
            else:
                data.add_other_data(other_data_names[i], value)
        return
