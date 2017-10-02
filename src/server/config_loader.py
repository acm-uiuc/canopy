import yaml


def load(config_file):
    try:
        with open(config_file, "r") as stream:
            return yaml.load(stream)
    except yaml.YAMLError:
        raise yaml.YAMLError("Failed to parse config YAML")
    except IOError:
        raise IOError("Failed to open/read config YAML")
