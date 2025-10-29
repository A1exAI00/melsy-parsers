from typing import List, Dict, Tuple
import re

from backend.misc import (
    convert_timedelta_to_hours,
    convert_string_to_timedelta,
    normalize_time,
    convert_hours_float_to_timedelta,
    convert_timedelta_to_string,
    convert_to_float_or_nan,
)

ABSOLUTE_TIME_PATTERN = r"\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}"
RELETIVE_TIME_PATTERN = r"\d+:\d{2}:\d{2}"
NUMBER_PATTERN = r"[-+]?\d*\.?\d+|NaN|nan|NAN"
NOTHING_PATTERN = r"$a"


class LTdata:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.GIVIK_version = None

        self.lines: List[str] = []
        self.LT: Dict[str, List[float | str]] = {}
        self.other_data: Dict = {}
        return

    def add_lines(self, lines: List[str]) -> None:
        self.lines = lines
        return

    def add_LT(self, name: str, values: List[float]) -> None:
        # TODO check if name is in keys already
        self.LT[name] = values
        return

    def add_other_data(self, name: str, value) -> None:
        self.other_data[name] = value
        return


class LTparser:
    def __init__(self) -> None:
        return

    def get_lines(self, data: LTdata) -> None:
        lines = []
        with open(data.filepath, "r", errors="ignore") as file:
            lines = file.readlines()
        data.lines = lines
        return

    def parse(self, filepath: str) -> LTdata:
        data = LTdata(filepath)
        self.get_lines(data)
        self.parse_GIVIK_version(data)
        self.parse_LT(data)
        self.parse_other_data(data)
        return data

    def parse_GIVIK_version(self, data: LTdata) -> None:
        first_line = data.lines[0]
        if re.search(r"^#{96}$", first_line):
            data.GIVIK_version = 1
        elif re.search(r"^#{258}$", first_line):
            data.GIVIK_version = 2
        else:
            raise Exception(
                f"Could not determin GIVIK version for file: {data.filepath}"
            )
        return

    def parse_LT(self, data: LTdata) -> None:
        match data.GIVIK_version:
            case 1:
                self.parse_LT_GIVIK1(data)
            case 2:
                self.parse_LT_GIVIK2(data)
            case _:
                raise Exception(f"Unknown GIVIK version: {data.GIVIK_version}")
        return

    def parse_LT_GIVIK1(self, data: LTdata) -> None:
        last_line_with_marker = -1
        for line_i, line in enumerate(data.lines):
            my_matches = re.findall(r"^-{96}$", line)
            if my_matches:
                last_line_with_marker = line_i

        if last_line_with_marker == -1:
            raise Exception(f"Could not find LT start in file: {data.filepath}")

        LT_start_line_i = last_line_with_marker + 1
        LT_end_line_i = len(data.lines) - 1

        times_str: List[str] = []
        times_float: List[float] = []
        powers: List[float] = []
        for line_i in range(LT_start_line_i, LT_end_line_i):
            line = data.lines[line_i]

            # abs_time = re.findall(self.abs_date_pattern, line)[0]
            rel_time = re.findall(RELETIVE_TIME_PATTERN, line)[-1]
            power = re.findall(NUMBER_PATTERN, line)[-1]

            times_str.append(rel_time)
            times_float.append(
                round(
                    convert_timedelta_to_hours(convert_string_to_timedelta(rel_time)),
                    ndigits=5,
                )
            )
            powers.append(convert_to_float_or_nan(power))

        data.add_LT("Reletive time", times_str)
        data.add_LT("Reletive time, h", normalize_time(times_float))
        data.add_LT("Power (avg), W", powers)
        return

    def parse_LT_GIVIK2(self, data: LTdata) -> None:
        section_start_is = []
        for i, line in enumerate(data.lines):
            my_matches = re.findall(r"^#{258}$", line)
            if my_matches:
                section_start_is.append(i)
        section_start_is.append(len(data.lines) - 1)

        LT_start_is = []
        LT_end_is = []
        for section_i in range(len(section_start_is) - 1):
            section_start_i = section_start_is[section_i]
            section_end_i = section_start_is[section_i + 1]
            LT_start_i = -1
            for line_i in range(section_start_i, section_end_i):
                if re.findall(r"^-{261}$", data.lines[line_i]):
                    LT_start_i = line_i

            LT_start_is.append(LT_start_i)
            LT_end_is.append(section_end_i)

        rel_time_str_all = []
        current_all = []
        voltage_all = []
        power_avg_all = []
        temperature_all = []
        for section_i in range(len(section_start_is) - 1):
            section_start_line_i = LT_start_is[section_i] + 1
            section_end_line_i = LT_end_is[section_i]

            for line_i in range(section_start_line_i, section_end_line_i):
                line = data.lines[line_i]

                # abs_date = re.findall(ABSOLUTE_TIME_PATTERN, line)[0]
                rel_time = re.findall(RELETIVE_TIME_PATTERN, line)[-1]
                # pulse_count = re.findall(NUMBER_PATTERN, line)[0]
                current = re.findall(NUMBER_PATTERN, line)[9]
                voltage = re.findall(NUMBER_PATTERN, line)[10]
                power_avg = re.findall(NUMBER_PATTERN, line)[11]
                # power_imp = re.findall(NUMBER_PATTERN, line)[12]
                tank_water_temp = re.findall(NUMBER_PATTERN, line)[13]

                rel_time_str_all.append(rel_time)
                current_all.append(convert_to_float_or_nan(current))
                voltage_all.append(convert_to_float_or_nan(voltage))
                power_avg_all.append(convert_to_float_or_nan(power_avg))
                temperature_all.append(convert_to_float_or_nan(tank_water_temp))

        timedeltas = [convert_string_to_timedelta(each) for each in rel_time_str_all]
        float_times = [convert_timedelta_to_hours(each) for each in timedeltas]
        float_times = [round(each, ndigits=5) for each in float_times]
        normal_float_times = normalize_time(float_times)

        normal_timedeltas = [
            convert_hours_float_to_timedelta(each) for each in normal_float_times
        ]
        normal_time_strings = [
            convert_timedelta_to_string(each) for each in normal_timedeltas
        ]

        data.add_LT("Reletive time", normal_time_strings)
        data.add_LT("Reletive time, h", normal_float_times)
        data.add_LT("Current, A", current_all)
        data.add_LT("Voltage, V", voltage_all)
        data.add_LT("Power (avg), W", power_avg_all)
        data.add_LT("Tank water temp., C", temperature_all)
        return

    def parse_other_data(self, data: LTdata) -> None:
        match data.GIVIK_version:
            case 1:
                self.parse_other_data_GIVIK1(data)
            case 2:
                self.parse_other_data_GIVIK2(data)
            case _:
                raise Exception(f"Unknown GIVIK version: {data.GIVIK_version}")
        return

    def parse_other_data_GIVIK1(self, data: LTdata) -> None:
        return

    def parse_other_data_GIVIK2(self, data: LTdata) -> None:
        other_data_patterns = [
            r"Pulse width:\s*([0-9]*\.?[0-9]+)\s*ms",
            r"Repetition frequency:\s*([0-9]*\.?[0-9]+)\s*Hz",
            r"Set operating current:\s*([0-9]*\.?[0-9]+)\s*A",
        ]
        other_data_names = [
            "Pulse width, ms",
            "Repetition frequency, Hz",
            "Set operating current, A",
        ]
        for pattern_i, pattern in enumerate(other_data_patterns):
            for line in data.lines:
                if re.findall(pattern, line):
                    value = re.findall(NUMBER_PATTERN, line)[0]
                    data.add_other_data(
                        other_data_names[pattern_i], convert_to_float_or_nan(value)
                    )
        return
