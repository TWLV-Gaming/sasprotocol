import yaml

class configHandler:
    def __init__(self, file_path="/Users/jakewatts/12 Gaming/twlvgaming/sasprotocol/config.yml"):
        self.config_file_path = file_path
        self.config = None

    def read_config_file(self):
        try:
            with open(self.config_file_path, "r") as yaml_file:
                self.config = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"The configuration file {self.config_file_path} was not found.")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing the YAML file: {e}")

    def get_config_value(self, section, key):
        if self.config:
            return self.config.get(section, {}).get(key)
        else:
            raise ValueError("Configuration not loaded. Call read_config_file first.")

