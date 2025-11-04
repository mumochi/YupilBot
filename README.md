# YupilBot
A custom Discord bot with moderation and communication tools.

## Adding the bot to a server
Go to https://discord.com/developers/applications. Create a New Application with whatever name you like. You can put it into a team if you have multiple members managing the bot. In the left pane, go to Installation. Navigate to Install Link and set it to None and apply changes. 

Navigate to the Bot tab in the left pane. Turn off Public Bot, turn on Server Members Intent and Message Content Intent.

Navigate to the OAuth tab in the left pane. Select bot and applications.commands scopes. Copy the generated URL at the bottom and paste that into your browser. This will add the bot to the server.

### Permissions:
#### General:
```
View Audit Log
Manage Roles
Manage Channels
Kick Members
Ban Members
View Channels
Moderate Members
```
#### Text:
```
Send Messages
Send Messages In Threads
Manage Messages
Embed Links
Attach Files
Read Message History
Mention Everyone
Use External Emojis
Use External Stickers
Add Reactions
```
#### Voice:
```
Move Members
```

Lastly go back to the Bot tab. Click on the Reset Token button and copy that token. You will need that later for the first-time setup to generate an `.env` environment file.

## Installation
First, clone the YupilBot github repository. This directory is the location where all of the local setup will be done.
```shell
git clone https://github.com/mumochi/YupilBot.git
cd YupilBot
```

### Prerequisites
YupilBot minimally requires Python plus package dependencies installed on the bot host server or machine. If using Docker, you can skip the Python and Python package installations.  
  
  
* **Python:** YupilBot uses Python 3.13.7. You can download it here: https://www.python.org/downloads/release/python-3137/  
Alternatively, for compatibility and portability, we have prepared a package-complete Dockerfile with build instructions [here](docker). 

* **Python packages:** Packages and package versions required for running YupilBot are included in [requirements.txt](requirements.txt).  
Once Python has been installed, we recommend creating a virtual environment for YupilBot packages. You can do so by running:
```
python3 -m venv yupilbot
source yupilbot/bin/activate
python3 -m pip install -r requirements.txt
```

* **Docker (optional):** To install Docker on your system, look for system-specific instructions here: https://docs.docker.com/engine/install/  
Once Docker has been installed, you can build the YupilBot Docker image from the included Dockerfile by running:
```shell
docker build -t yupilbot ./docker/
```
This creates a local `yupilbot:latest` Docker image containing Python 3.13.7 and all of the package dependencies.

### First-time setup
Once Python 3.13.7 and all of the package dependencies are available, either through direction installation or with the Docker image, first-time setup can be run from [setup.py](setup.py), which will generate a production `.env` environment file and a configuration `config.ini` file.

To run from a direct installation, make sure you're in the root YupilBot directory and run:
```shell
source yupilbot/bin/activate
python3 setup.py
```
To run using the Docker image:
```shell
docker run -it -v .:/yupilbot yupilbot:latest python3 setup.py
```
The setup script will take you through all of the steps needed to configure the bot environment, including supplying a Discord server ID and bot token, as well as other configurable options such as which server channels to use as bot log channels. If successful, the bot will authenticate and connect to the Discord server, and the script will generate `.env` and `config.ini` files which you can manually edit as desired later.
#### config.ini setting descriptions
* `log_channel`:  Where you want a majority of logs to go.
* `priority_log_channel`: Where you want important logs to go (e.g., spammer detection).
* `welcome_channel`: Your server's welcome channel.
* `all_role`: Cosmetic role that is given to every user upon first joining the server.
* `vc_role`: Role that is given so users can see voice channels. Given automatically 15 minutes after a member joins to discourage malicious activity.
* `cache_size`: Number of messages to keep in memory, no commas. 20000 seems to use ~2GB of RAM.
* `disable_webcams`: Automatically disconnects members if they turn their webcams on with a message if True.
* `disable_external_forwarding`: Automatically deletes forwarded messages originating from external servers if True.
* `message_spam_age`: Age of messages in seconds when detecting spam (e.g., check messages sent in the last 60 seconds).
* `message_spam_cache`: How many messages to compare for spam detection (e.g., compare the contents of the last 3 messages).
  
If manually editing the `config.ini`, you can get these IDs by right clicking on individual channels or on Server Settings -> Roles for role IDs.

## Running YupilBot
Once everything has been successfully installed and the first-time setup has been completed, YupilBot should be ready to run. Double-check all permission settings for YupilBot on your server to make sure it has access to channels, moderation commands, etc. Also make sure that only moderators are able to use its commands via the server Integrations settings.  


### Environment 
YupilBot uses the `YUPIL_ENV` environment variable to know which .env file to read. This will preferably be prod (production) for your main instance of Yupil Bot and anything else for your testing versions. Here, we'll assume a prod rather than a development environment, though you can edit this as necessary. (Note: if you have multiple users or don't want to set it each time, you can set `YUPIL_ENV` in `/etc/environment` so that it applies to all users by adding the line: `YUPIL_ENV=prod`).  

### Setting up a tmux session
We highly recommend setting up a tmux session. Tmux is handy to keep the YupilBot session alive after you disconnect (e.g., if you're connecting to a remote server instance); otherwise, it might kill your instance of YupilBot after some time. This should already be installed if you're running Ubuntu 24.04 or other common Linux distributions. This is a handy cheat sheet for the commands if you don't use it often: https://tmuxcheatsheet.com/  
Create a new session:
```shell
tmux new -s <sessionName>
```
You can then attach to the session and execute your commands as normal. Ctrl+b then d will disconnect you from the tmux session.

### Running
To run from a direction installation:
```shell
export YUPIL_ENV=prod
source yupilbot/bin/activate
python3 main.py
```
To run using the Docker image:
```shell
docker run -e YUPIL_ENV=prod -v .:/yupilbot yupilbot:latest python3 main.py
```
