# Config module to establish shared variables

import os
import configparser
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_file: str) -> None:
        yupil_env = os.getenv("YUPIL_ENV")
        if yupil_env != "prod":
            load_dotenv(".env.local")
        else:
            load_dotenv(".env")
        self.server_id = os.getenv("DISCORD_SERVER_ID")
        self.token = os.getenv("DISCORD_TOKEN")
        # Read config info
        config = configparser.ConfigParser()
        config.read(config_file)
        config_env = config[yupil_env]
        self.welcome_channel = int(config_env['welcome_channel'])
        self.log_channel = int(config_env['log_channel'])
        self.priority_log_channel = int(config_env['priority_log_channel'])
        self.max_messages = int(config_env['cache_size'])
        self.all_role = config_env['all_role'] # Cosmetic role assigned to every member upon joining
        self.vc_role = config_env['vc_role'] # Role assigned allowing VC access
        self.disable_webcams = eval(config_env['disable_webcams'])