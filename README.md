# YupilBot
Custom Discord bot with basic chat functions, implemented with slash commands

### Features
1. Chat command to send a message to a text channel on a server
   * Intended as a moderation tool to send moderation team messages to the server from a single "anonymous" bot account

2. DM command to send direct message to specific member on a server with simple logging
   * Intended as a moderation tool to send DMs to individual members from a single "anonymous" bot account

3. Chat commands to restrict and unrestrict a member's ability to view text and voice channels
   * Intended as a moderation tool to isolate members - unable to see or interact with text and voice channels
   * Also unable to view server member list, which can prevent unwanted DMs from suspected bots or malicious users
   * Can be used in conjunction with ticket tool features to subsequently create a specific channel
     to facilitate discussions with the moderation team while maintaining isolation

4. Translation command leveraging the DeepL API to translate text to English (EN-US)
   * Intended to provide robust one-way translation of non-English text to English
   * Free version of the DeepL API allows for up to 500,000 translated characters per month
     
5. Transcript creation

6. Ticket tool system

7. Logging of edited and deleted messages

8. More!! Will be updating documentation in future updates.


### Setup
* Create a .env file at the same level as YupilBot.py with the keys: DISCORD_API, DEEPL_API_TOKEN, DISCORD_SERVER_ID. Insert your generated keys for your Discord application/bot key and DeepL API key into the relevant fields.
* Optionally create a .env.local file with the same key names as the .env but with the necessary keys for a different server.
* Changes the values in config.ini for your server. prod is the default config, additional configs can be defined and used.
* You may need to generate a python requirements.txt file from the source if you do not have all libraries already installed.
* Run YupilBot.py
