# YB-rewrite
Rewrite of the original YupilBot

## Configuration
YupilBot uses two libraries to load in sensitive data such as bot keys and to initialize guild-specific settings such as channel IDs:
* [dotenv](https://pypi.org/project/python-dotenv/)
* [configparser](https://docs.python.org/3/library/configparser.html)

A minimal example shows how they work:
```python
import os
import configparser
from dotenv import load_dotenv

if os.getenv("YUPIL_ENV") != "prod":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")
```

In this first code snippet, `os.getenv` searches the Python launch environment for the `YUPIL_ENV` key. We define this environmental variable in a VS Code debugging launch.json file. If running outside of a debugging environment, you will need to set the environment variable before running the bot:
```shell
export YUPIL_ENV="prod"
python3 main.py
```

The .env and .env.local files contain sensitive information like bot keys. Do not expose these publicly. With `YUPIL_ENV` set, `dotenv` can now read one of the .env files, giving us the server ID and bot token:
```python
server_id = os.getenv("DISCORD_SERVER_ID")
token = os.getenv("DISCORD_TOKEN")
```

The remaining guild-specific variables are set in a config.ini file and read into the program using `configparser`:
```python
config = configparser.ConfigParser()
config.read("config.ini")

welcome_channel = int(config[os.getenv('YUPIL_ENV')]['welcome_channel'])
permitted_role = config[os.getenv('YUPIL_ENV')]['permitted_role']  # Only users with this role can use the commands
max_messages = int(config[os.getenv('YUPIL_ENV')]['cache_size'])
```

See the templates directory for env and config templates.
