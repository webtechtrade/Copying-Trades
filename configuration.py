import json
import os


class Configuration:
    config = None

    def __init__(self):
        filename = os.path.abspath(__file__).replace(__name__ + ".py", "") + "config.json"
        with open(filename, 'r') as f:
            self.config = json.load(f)
