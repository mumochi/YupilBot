# YupilBot
Custom Discord bot with basic chat functions, implemented with slash commands

### Basic features
1. Chat command to send message to a text channel on a server
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/87c1b4fc-fd62-4d7a-b4e0-8a9a486cfc38)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/a0549c50-7d30-45d6-8468-b2168f7eebf2)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/2f3a1a3b-c48a-47dc-8909-44498ff0dfcb)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/1601086b-3679-4bef-94b9-53a03e851c8b)

2. DM command to send direct message to specific member on a server with simple logging
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/ad259bb6-4583-48a9-b0ac-74558a374864)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/5c502121-ebf7-465e-b1b5-69bfc18df29f)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/452ff24f-356b-4f1b-b93f-96585221583d)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/c14132a6-4911-4252-a41b-9b8f7c9dfbbf)
  ![image](https://github.com/mumochi/YupilBot/assets/149116223/6cd7adc4-409a-40ae-9ebd-05a0d6aaa678)

3. Translation command leveraging the DeepL API to translate text to English (EN-US)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/0db815c5-38f6-4ccb-8b8a-450bed30d8ff)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/2525d983-93c9-49df-bda4-902be6c42bd6)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/9cb33fb2-3b49-4ff2-bb03-915dd420a2d1)
   ![image](https://github.com/mumochi/YupilBot/assets/149116223/63654aa2-119f-4d76-a2c3-4f170c24cb62)



### Setup
* Fill in server-specific values for `server_id` and `permitted_role`
* Ensure proper role configuration for command permissions
* Generate a [DeepL authentication key](https://developers.deepl.com/docs/getting-started/auth), copy to deepl_key.txt, and place deepl_key.txt in the YupilBot.py directory
* Generate a [Discord bot token](https://discord.com/developers/docs/topics/oauth2), copy to token.txt, and place token.txt in the YupilBot.py directory
* Run YupilBot.py
