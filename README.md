# YupilBot
Custom Discord bot with basic chat functions, implemented with slash commands

### Features
1. Chat command to send a message to a text channel on a server
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/87c1b4fc-fd62-4d7a-b4e0-8a9a486cfc38)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/a0549c50-7d30-45d6-8468-b2168f7eebf2)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/2f3a1a3b-c48a-47dc-8909-44498ff0dfcb)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/1601086b-3679-4bef-94b9-53a03e851c8b)
   * Intended as a moderation tool to send moderation team messages to the server from a single "anonymous" bot account

2. DM command to send direct message to specific member on a server with simple logging
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/ad259bb6-4583-48a9-b0ac-74558a374864)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/5c502121-ebf7-465e-b1b5-69bfc18df29f)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/452ff24f-356b-4f1b-b93f-96585221583d)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/c14132a6-4911-4252-a41b-9b8f7c9dfbbf)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/6cd7adc4-409a-40ae-9ebd-05a0d6aaa678)
   * Intended as a moderation tool to send DMs to individual members from a single "anonymous" bot account

3. Chat commands to restrict and unrestrict a member's ability to view text and voice channels
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/9d82a559-1339-4d71-8ee6-9f5c04a51ec6)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/29b56e2d-b74f-4f17-b121-a628ad0386e0)
   * Intended as a moderation tool to isolate members - unable to see or interact with text and voice channels
   * Also unable to view server member list, which can prevent unwanted DMs from suspected bots or malicious users
   * Can be used in conjunction with bots like Ticket Tool to subsequently create a specific channel
     to facilitate discussions with the moderation team while maintaining isolation

4. Translation command leveraging the DeepL API to translate text to English (EN-US)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/0db815c5-38f6-4ccb-8b8a-450bed30d8ff)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/2525d983-93c9-49df-bda4-902be6c42bd6)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/9cb33fb2-3b49-4ff2-bb03-915dd420a2d1)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/63654aa2-119f-4d76-a2c3-4f170c24cb62)
   * Intended to provide robust one-way translation of non-English text to English
   * Free version of the DeepL API allows for up to 500,000 translated characters per month
5. A lot more stuff we need to add to this page.



### Setup
* Create a .env file at the same level as YupilBot.py with the keys: DISCORD_API, DEEPL_API_TOKEN, DISCORD_SERVER_ID. Insert your generate keys for your Discord application/bot key and DeepL API key into the relavent fields.
* Optionally create a .env.local file with the same key names as the .env but with the necessary keys for a different server.
* Changes the values in config.ini for your server. prod is the default config, additional configs can be defined and used.
* You may need to generate a python requirements.txt file from the source if you do not have all libraries already installed.
* Run YupilBot.py
