import pandas as pd
import requests
from io import StringIO

competition_links = pd.read_csv(r"./competition_links.csv").set_index("COMPETITION")["URL"].to_dict()
roster_links = pd.read_csv(r"./roster_links.csv").set_index("ALIAS")["URL"].to_dict()
teams_mapping = pd.read_csv(r"./teams_mapping.csv")

def download_hokej_stats() -> None:
    raw_list = load_raw_list(competition_links)
    processed = process_raw_list(raw_list)
    numbered = merge_numbers(processed)
    numbered.to_csv("../Raw/raw.csv", index=False)


def load_raw_list(competitions_dict: dict[str, str]) -> list[pd.DataFrame]:
    data_list = []
    for _, link in competitions_dict.items():
        response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
        all_tables = pd.read_html(StringIO(response.text))
        for tab in all_tables:
            if "JMÉNO" in tab.columns:
                data_list.append(tab)
    return data_list


def process_raw_list(raw_list: list[pd.DataFrame]) -> pd.DataFrame:
    data = pd.concat(raw_list)
    data = data[["JMÉNO", "TÝM", "POZ."]]
    unique_rows = data.drop_duplicates()
    data_names = process_names(unique_rows, "JMÉNO")
    data_final = data_names.merge(teams_mapping,
        left_on="TÝM", right_on="LONG", how="left"
    )
    data_final = data_final.rename(
        columns={"ALIAS":"team", "POZ.": "pos"}
    )
    return data_final[["surname", "name", "team", "pos"]]


def process_names(data: pd.DataFrame, name_col: str) -> pd.DataFrame:
    parts = data[name_col].str.split()
    data["surname"] = parts.str[-1]
    data["name"] = parts.str[:-1].str.join(" ")
    data = data.drop(columns=[name_col])
    return data


def merge_numbers(data: pd.DataFrame) -> pd.DataFrame:
    rosters = load_rosters(roster_links)
    data = data.merge(rosters, on=["surname", "name", "team"], how="outer")
    return data


def load_rosters(links_dict: dict[str, str]) -> pd.DataFrame:
    roster_list = []
    for team, link in links_dict.items():
        response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
        all_tables = pd.read_html(StringIO(response.text))
        for tab in all_tables:
            if "Hráč" in tab.columns:
                tab["team"] = team[:3]
                roster_list.append(tab)
    roster_data = pd.concat(roster_list)
    rosters_with_names = process_names(roster_data, "Hráč")
    rosters_with_names = rosters_with_names.drop_duplicates()
    return rosters_with_names[["surname", "name", "team", "#"]]


def main() -> int:
    download_hokej_stats()
    return 0


if __name__ == "__main__":
    from sys import exit
    exit(main())
