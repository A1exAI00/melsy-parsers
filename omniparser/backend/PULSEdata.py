from typing import List, Tuple, Dict
from math import nan

import re

from backend.misc import convert_to_float_or_nan

NUMBER_PATTERN = r"[-+]?\d*\.?\d+|NaN|nan|NAN"


class PULSEdata:
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

        self.lines: List[str] = []
        self.mode = None
        self.LIV: Dict[str, List[float | str]] = {}
        self.intensity: Dict[str, List[float | str]] = {}
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


class PULSEparser:
    def __init__(self) -> None:
        return

    def get_lines(self, data: PULSEdata) -> None:
        lines = []
        with open(data.filepath, "r", errors="ignore") as file:
            lines = file.readlines()
        data.lines = lines
        return

    def parse(self, filepath: str) -> PULSEdata:
        data = PULSEdata(filepath)
        self.get_lines(data)
        self.get_mode(data)
        if "LIV" in data.mode:
            self.parse_LIV(data)
        if "Spectrum" in data.mode:
            self.parse_spectrum(data)
            self.parse_intensity(data)
        return data

    def get_mode(self, data: PULSEdata) -> None:
        data.mode = data.lines[0]
        return

    def parse_LIV(self, data: PULSEdata) -> None:
        LIV_section_markers: List[str] = [
            "**************",
        ]

        section_is = []
        for section_marker in LIV_section_markers:
            for i, line in enumerate(data.lines):
                if section_marker in line:
                    section_is.append(i)

        if not section_is:
            return

        i = section_is[0]
        while not re.findall(NUMBER_PATTERN, data.lines[i]):
            i += 1

        current_all = []
        power_all = []
        voltage_all = []
        current_monitor = []
        while foundall := re.findall(NUMBER_PATTERN, data.lines[i]):
            current_all.append(convert_to_float_or_nan(foundall[0]))
            power_all.append(convert_to_float_or_nan(foundall[1]))
            voltage_all.append(convert_to_float_or_nan(foundall[2]))
            current_monitor.append(convert_to_float_or_nan(foundall[3]))
            i += 1

        data.add_LIV("Current, A", current_all)
        data.add_LIV("Power, W", power_all)
        data.add_LIV("Voltage, V", voltage_all)
        data.add_LIV("Current Monitor, mV", current_monitor)
        return

    def parse_spectrum(self, data: PULSEdata) -> None:
        LIV_section_markers: List[str] = [
            "**************",
        ]

        section_is = []
        for section_marker in LIV_section_markers:
            for i, line in enumerate(data.lines):
                if section_marker in line:
                    section_is.append(i)

        if not section_is:
            return

        i = section_is[0]
        while not re.findall(NUMBER_PATTERN, data.lines[i]):
            i += 1

        current_all = []
        fwhm_all = []
        mean_wl_all = []
        max_wl_all = []
        dispersion_all = []
        while foundall := re.findall(NUMBER_PATTERN, data.lines[i]):
            current_all.append(convert_to_float_or_nan(foundall[0]))
            fwhm_all.append(convert_to_float_or_nan(foundall[1]))
            mean_wl_all.append(convert_to_float_or_nan(foundall[2]))
            max_wl_all.append(convert_to_float_or_nan(foundall[3]))
            dispersion_all.append(convert_to_float_or_nan(foundall[4]))
            i += 1

        data.add_LIV("Current, A", current_all)
        data.add_LIV("FWHM, nm", fwhm_all)
        data.add_LIV("Mean WL, nm", mean_wl_all)
        data.add_LIV("Max WL, nm", max_wl_all)
        data.add_LIV("Dispersion", dispersion_all)
        return

    def match_line_with_pattern(self, data: PULSEdata, pattern: str) -> str:
        for line in data.lines:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return

    def parse_other_data(self, data: PULSEdata) -> None:
        other_data_patterns: List[str] = [
            r"Pulse Width:\s+([0-9]*\.?[0-9]+)\s+ns",
            r"Period:\s+([0-9]*\.?[0-9]+)\s+us" r"Frequency:\s*([0-9]*\.?[0-9]+)Hz",
        ]
        other_data_names: List[str] = ["Duration, us", "Frequency, Hz"]
        for i, pattern in enumerate(other_data_patterns):
            value: str = self.match_line_with_pattern(data, pattern)
            data.add_other_data(other_data_names[i], convert_to_float_or_nan(value))
        return

    def parse_intensity(self, data: PULSEdata) -> None:
        table_header_pattern = r"Current, A\s+\d+\s+"
        for line_i, line in enumerate(data.lines):
            if re.match(table_header_pattern, line):
                break
        else:
            return

        current_all = re.findall(NUMBER_PATTERN, data.lines[line_i])
        intensity_all = {}
        for current in current_all:
            intensity_all[f"Intensity (current={current}A)"] = []

        wl_all = []
        for i in range(line_i + 2, len(data.lines)):
            line = data.lines[i]
            foundall = re.findall(NUMBER_PATTERN, line)
            if not foundall:
                break
            wl_all.append(convert_to_float_or_nan(foundall[0]))
            for j, current in enumerate(current_all):
                intensity_all[f"Intensity (current={current}A)"].append(
                    convert_to_float_or_nan(foundall[j + 1])
                )

        data.add_LIV("Current, A", current_all)
        data.add_LIV("Wavelength, nm", wl_all)
        data.LIV.update(intensity_all)
        return
