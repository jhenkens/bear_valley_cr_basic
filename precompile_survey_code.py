#! /usr/bin/env python3
import yaml
import jinja2
import pathlib


CURRENT_FILE = pathlib.Path(__file__)
BASE_DIR = CURRENT_FILE.parent
TEMPLATES_DIR: pathlib.Path = BASE_DIR / "Templates"
INCLUDE_DIR = TEMPLATES_DIR / "Include"
YAML_FILE = TEMPLATES_DIR / "surveys.yaml"
TEMPLATE_FILE = TEMPLATES_DIR / "Survey.CRB"

    

extensions = {"CR300": "CR300", "CR1000": "CR1", "CR6": "CR6"}
if __name__ == "__main__":
    with open(TEMPLATE_FILE, "r") as template_file_raw:
        template_file = template_file_raw.read()

    with open(YAML_FILE, "r") as yaml_file_raw:
        survey_config = yaml.safe_load(yaml_file_raw.read())

    shared_config = survey_config.get("shared", None) or {}
    for station in survey_config.get("stations", None):
        model_series = station["model_series"]
        def find_template(s):
            for p in [
                INCLUDE_DIR / "Stations" / station["station_name"] / s,
                INCLUDE_DIR / "Models" / model_series / s,
                INCLUDE_DIR / s,
            ]:
                if p.is_file():
                    return str(p.relative_to(TEMPLATES_DIR))
            raise FileNotFoundError(f"Template {s} not found")

        model_config = survey_config.get(model_series, None) or {}
        station_config = {**shared_config, **model_config, **station}

        file_name = station_config["station_name"]
        extension = extensions[model_series]

        dest_file_name = BASE_DIR / f"{file_name}.{extension}"

        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
            lstrip_blocks=True,
            trim_blocks=True,
        )
        env.globals["find_template"] = find_template
        template = env.from_string(template_file)
        try:
            content = template.render(**station_config)
        except Exception as e:
            print(f"Error in {file_name}")
            raise

        with open(dest_file_name, "w") as dest_file:
            dest_file.write(content)
