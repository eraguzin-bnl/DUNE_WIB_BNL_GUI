#!/usr/bin/env python3
import configparser
import os

class CheckoutScript():
    def __init__(self,config_path):
        print("Configuring WIB")
        self.parse_config(config_path)
        
    def parse_config(self, config_path):
        try:
            config.read(config_path, encoding='utf-8')
            self.wib_address = config["DEFAULT"]["WIB_ADDRESS"]
        except:
            print(f"Error: Config file not found at {config_path}. Using default values")
            self.wib_address = "192.168.121.1"


if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "settings_configure.json")
    CheckoutScript(config_path)
