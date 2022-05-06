#!/usr/bin/env python3
import configparser
import os

class CheckoutScript():
    def __init__(self,config_path):
        print("we'e here")


if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "settings_checkout.ini")
    CheckoutScript(config_path)
