#!/usr/bin/env python3
import configparser
import os
import json

class CheckoutScript():
    def __init__(self,config_path):
        print("Configuring WIB")
        self.parse_config(config_path)
        
    def parse_config(self, config_path):
        try:
            f = open(config_path)
            wib = json.load(f)
        except FileNotFoundError:
            print(f"Error: Config file not found at {config_path}. Using default values")
            self.wib_address = "192.168.121.1"

#        except json.decoder.JSONDecodeError:
#            print("JSON file malformed")

        for i in wib:
            print(i)
            print(wib[i])

        print(wib['femb1']['channel_setting'])


if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "settings_configure.json")
    CheckoutScript(config_path)
