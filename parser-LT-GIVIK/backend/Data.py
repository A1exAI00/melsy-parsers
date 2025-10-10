from typing import List, Dict, Tuple

import re
from datetime import timedelta


class Data:
    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.lines: List[str] = None

        # GIVIK version markers
        self.GIVIK_version = None
        self.GIVIK_version_patterns = [
            r"^#{96}$",
            r"^#{258}$"
        ]

        # LT markers for GIVIK1
        self.GIVIK1_LT_section_pattern = r"^-{96}$"

        # LT markers for GIVIK2
        self.GIVIK2_LT_section_pattern = r"^#{258}$"
        self.GIVIK2_LT_start_pattern = r"^-{261}$"

        # LT data
        self.LT: Dict = {}

        # Additional to LIV data
        self.GIVIK1_additional_data_section_marker = r"$a"
        self.GIVIK2_additional_data_section_marker = r"###	Operation condition	###"

        # Naming data
        self.naming_data: Dict[str, str] = {}

        self.abs_date_pattern = r"\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}"
        self.rel_time_pattern = r"\d+:\d{2}:\d{2}"
        self.number_pattern = r"[-+]?\d*\.?\d+|NaN|nan|NAN"
        return

    @property
    def is_invalid(self) -> bool:
        return (self.LT.keys() < 2)

    def add_naming(self, value) -> None:
        self.naming_data["Name"] = value
        return

    def get_naming(self) -> Tuple[str, str]:
        return ("Name", self.naming_data["Name"])

    def read_lines_from_file(self) -> None:
        with open(self.filepath, "r", errors="ignore") as file:
            self.lines = file.readlines()
        return

    def parse_GIVIK_version(self) -> None:
        first_line = self.lines[0]
        if re.search(self.GIVIK_version_patterns[0], first_line):
            self.GIVIK_version = 1
        elif re.search(self.GIVIK_version_patterns[1], first_line):
            self.GIVIK_version = 2
        else:
            raise Exception(
                f"Could not determin GIVIK version for file: {self.filepath}")

        match self.GIVIK_version:
            case 1:
                self.additional_data_names = ["Avg. power(time) slope, W/h",]
                self.additional_data_patterns = [r"$a",]
                self.additional_data_values = [None,] \
                    * len(self.additional_data_names)
            case 2:
                self.additional_data_names = [
                    "Pulse width, ms",
                    "Repetition frequency, Hz",
                    "Set operating current, A",
                    "Avg. power(time) slope, W/h"
                ]
                self.additional_data_patterns = [
                    r"Pulse width:\s*([0-9]*\.?[0-9]+)\s*ms",
                    r"Repetition frequency:\s*([0-9]*\.?[0-9]+)\s*Hz",
                    r"Set operating current:\s*([0-9]*\.?[0-9]+)\s*A",
                    r"$a"
                ]
                self.additional_data_values = [None,] \
                    * len(self.additional_data_patterns)
        return

    def parse_LT(self) -> None:
        match self.GIVIK_version:
            case 1:
                self.parse_LT_GIVIK1()
                self.parse_power_slope_GIVIK1()
            case 2:
                self.parse_LT_GIVIK2()
                self.parse_power_slope_GIVIK2()
            case _:
                raise Exception(f"Unknown GIVIK version: {self.GIVIK_version}")

        return

    def parse_power_slope_GIVIK1(self) -> None:
        p1, p2 = self.LT["Power (avg), W"][0], self.LT["Power (avg), W"][-1]
        t1, t2 = self.LT["Reletive time, h"][0], self.LT["Reletive time, h"][-1]
        slope = (p2-p1)/(t2-t1)
        self.additional_data_values[0] = f"{slope:.5E}"
        return

    def parse_power_slope_GIVIK2(self) -> None:
        p1, p2 = self.LT["Power (avg), W"][0], self.LT["Power (avg), W"][-1]
        t1, t2 = self.LT["Reletive time, h"][0], self.LT["Reletive time, h"][-1]
        slope = (p2-p1)/(t2-t1)
        self.additional_data_values[3] = f"{slope:.5E}"
        return

    def parse_LT_GIVIK1(self) -> None:
        last_line_with_marker = -1
        for (line_i, line) in enumerate(self.lines):
            my_matches = re.findall(self.GIVIK1_LT_section_pattern, line)
            if my_matches:
                last_line_with_marker = line_i

        if last_line_with_marker == -1:
            raise Exception(
                f"Could not find LT start in file: {self.filepath}")

        LT_start_line_i = last_line_with_marker + 1
        LT_end_line_i = len(self.lines)-1

        times_str: List[str] = []
        times_float: List[float] = []
        powers: List[float] = []
        for line_i in range(LT_start_line_i, LT_end_line_i):
            line = self.lines[line_i]

            # abs_time = re.findall(self.abs_date_pattern, line)[0]
            rel_time = re.findall(self.rel_time_pattern, line)[-1]
            power = re.findall(self.number_pattern, line)[-1]

            times_str.append(rel_time)
            times_float.append(round(convert_timedelta_to_hours(
                convert_string_to_timedelta(rel_time)), ndigits=5))
            powers.append(float(power))

        self.LT["Reletive time"] = times_str
        self.LT["Reletive time, h"] = normalize_time(times_float)
        self.LT["Power (avg), W"] = powers
        return

    def parse_LT_GIVIK2(self) -> None:
        section_start_is = []
        for (i, line) in enumerate(self.lines):
            my_matches = re.findall(self.GIVIK2_LT_section_pattern, line)
            if my_matches:
                section_start_is.append(i)
        section_start_is.append(len(self.lines)-1)

        LT_start_is = []
        LT_end_is = []
        for section_i in range(len(section_start_is)-1):
            section_start_i = section_start_is[section_i]
            section_end_i = section_start_is[section_i+1]
            LT_start_i = -1
            for line_i in range(section_start_i, section_end_i):
                if re.findall(self.GIVIK2_LT_start_pattern, self.lines[line_i]):
                    LT_start_i = line_i

            LT_start_is.append(LT_start_i)
            LT_end_is.append(section_end_i)

        rel_time_str_all = []
        current_all = []
        voltage_all = []
        power_avg_all = []
        temperature_all = []
        for section_i in range(len(section_start_is)-1):
            section_start_line_i = LT_start_is[section_i] + 1
            section_end_line_i = LT_end_is[section_i]

            for line_i in range(section_start_line_i, section_end_line_i):
                line = self.lines[line_i]

                abs_date = re.findall(self.abs_date_pattern, line)[0]
                rel_time = re.findall(self.rel_time_pattern, line)[-1]
                pulse_count = re.findall(self.number_pattern, line)[0]
                current = re.findall(self.number_pattern, line)[9]
                voltage = re.findall(self.number_pattern, line)[10]
                power_avg = re.findall(self.number_pattern, line)[11]
                power_imp = re.findall(self.number_pattern, line)[12]
                tank_water_temp = re.findall(self.number_pattern, line)[13]

                rel_time_str_all.append(rel_time)
                current_all.append(float(current))
                voltage_all.append(float(voltage))
                power_avg_all.append(float(power_avg))
                temperature_all.append(float(tank_water_temp))

        timedeltas = [convert_string_to_timedelta(
            each) for each in rel_time_str_all]
        float_times = [convert_timedelta_to_hours(each) for each in timedeltas]
        float_times = [round(each, ndigits=5) for each in float_times]
        normal_float_times = normalize_time(float_times)

        normal_timedeltas = [convert_hours_float_to_timedelta(
            each) for each in normal_float_times]
        normal_time_strings = [convert_timedelta_to_string(
            each) for each in normal_timedeltas]

        self.LT["Reletive time"] = normal_time_strings
        self.LT["Reletive time, h"] = normal_float_times
        self.LT["Current, A"] = current_all
        self.LT["Voltage, V"] = voltage_all
        self.LT["Power (avg), W"] = power_avg_all
        self.LT["Tank water temp., C"] = temperature_all
        return

    def parse_additional_data(self) -> None:
        match self.GIVIK_version:
            case 1:
                self.parse_additional_data_GIVIK1()
            case 2:
                self.parse_additional_data_GIVIK2()
            case _:
                raise Exception(f"Unknown GIVIK version: {self.GIVIK_version}")
        return

    def parse_additional_data_GIVIK1(self) -> None:
        return

    def parse_additional_data_GIVIK2(self) -> None:
        for (pattern_i, pattern) in enumerate(self.additional_data_patterns):
            for (line_i, line) in enumerate(self.lines):
                if re.findall(pattern, line):
                    value = re.findall(self.number_pattern, line)[0]
                    self.additional_data_values[pattern_i] = value
        return

    def add_name(self, name: str) -> None:
        self.GIVI.insert(0, "Name")
        self.additional_data_values.insert(0, name)
        return


def convert_string_to_timedelta(string: str) -> timedelta:
    H, M, S = [int(each) for each in string.split(":")]
    return timedelta(hours=H, minutes=M, seconds=S)


def convert_timedelta_to_hours(delta: timedelta) -> float:
    return delta.total_seconds()/3600


def normalize_time(times: List[float]) -> List[float]:
    delta_t_threshold = 1  # h
    normal_time = [times[0],]
    base_time = 0.0
    for i in range(len(times)-1):
        t1, t2 = times[i], times[i+1]
        if abs(t2-t1) > delta_t_threshold:
            base_time += t1
        normal_time.append(base_time+t2)
    return normal_time


def convert_hours_float_to_timedelta(hours: float) -> timedelta:
    return timedelta(seconds=hours*3600)


def convert_timedelta_to_string(td: timedelta) -> str:
    D, S = td.days, td.seconds
    H = D*24 + S//3600
    rem_S = S % 3600
    M = rem_S//60
    rem_S = rem_S % 60
    HMS_strs = [str(H).rjust(2, "0"), str(
        M).rjust(2, "0"), str(rem_S).rjust(2, "0")]
    return ":".join(HMS_strs)
