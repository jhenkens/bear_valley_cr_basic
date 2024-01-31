#! /usr/bin/env python3
import yaml
import jinja2
import pathlib


CURRENT_FILE=pathlib.Path(__file__)
BASE_DIR = CURRENT_FILE.parent
YAML_FILE=BASE_DIR / "surveys.yaml"

extensions = {
    "cr300": "CR300",
    "cr1000": "CR1",
    "cr6": "CR6"
}
if __name__ == "__main__":
    with open(YAML_FILE,'r') as yaml_file_raw:
        survey_config = yaml.load(yaml_file_raw)
    for station in survey_config.get("stations",None):
        file_name = station["survey_name"]
        extension = extensions[station["model_series"]]
        dest_file = BASE_DIR / f"{file_name}.{extension}"