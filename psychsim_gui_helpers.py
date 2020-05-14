"""
This file has the classes and functions that are common across the gui windows
"""
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class PsychSimRun:
    id: str
    data: pd.DataFrame
    sim_file: str
    steps: int
    run_date: str = ""


@dataclass
class PsySimQuery:
    id: str
    data_id: str
    params: list
    function: str
    results: pd.DataFrame


if __name__ == "__main__":
    df = pd.DataFrame()
    test_data = PsychSimRun(id="test_id", run_date="date", data=df, sim_file="simfile", steps=9)
    print(asdict(test_data))
