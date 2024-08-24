# Yupil Bot function tests

Due to the nature of testing in Discord, which requires manual user input under normal circumstances, the following are non-exhaustive tests of Yupil Bot functions under expected or common conditions. For each set of conditions, an expected behavior and a result is indicated. 

## Tests
### **chat**
	* No reply, no embed
		* Expected: text sent as normal message to channel
		* Result: PASS
	* No reply, embed, no embed options
		* Expected: text sent as blank embed to channel
		* Result: PASS
	* Reply, no embed
		* Expected: text sent as reply to message in channel; if invalid message, send without reply
		* Result: PASS
	* Reply, embed, no embed options
		* Expected: text sent as embed reply to message in channel
		* Result: PASS
	* Reply, embed, embed title
		* Expected: text send as embed reply to message in channel with title
		* Result: PASS
	* Reply, embed, embed title, valid image URL (http, https; jpeg, png, gif)
		* Expected: text send as embed reply to message in channel with title and image
		* Result: PASS
	* Reply, embed, embed title, valid image URL, valid embed URL (http, https)
		* Expected: text send as embed reply to message in channel with title, image, and masked title link
		* Result: PASS
	* Reply, embed, embed title, valid image URL, valid embed URL, embed footer
		* Expected: text send as embed reply to message in channel with title, image, masked title link, and text footer
		* Result: PASS
### **create_buttons**
	* Expected: sends a message to the channel the command is run in that includes a ticket embed message with "Info Ticket" and "Mod Ticket" buttons that open modal UI text inputs when clicked
	* Result: PASS
### **dm**
	* Expected: message embed sent in DM to user and log sent to log channel
	* Result: PASS
### **kill_me**
	* Expected: bot process terminated with SystemExit
	* Result: PASS
### **log_dm_reply**
	* Text only
		* Expected: log with message content
		* Result: PASS
	* Single image attachment
		* Expected: log with image in embed
		* Result: PASS
	* Multiple image attachments
		* Expected: log with all images in bed
		* Result: PASS
	* Single non-image attachment
		* Expected: log with non-image attachment followup
		* Result: PASS
	* Multiple non-image attachments
		* Expected: log with multiple non-image attachments followup
		* Result: PASS
	* Mix of image and non-image attachments
		* Expected: log with images in embed and non-image attachments followup
		* Result: PASS
### **make_ticket**
	* Channel, no member added
		* Expected: creates a new ticket channel with input name and @everyone read permission disabled and mod role read and manage permissions enabled
		* Result: PASS
	* Channel, member added
		* Expected: creates a new ticket channel with input name and @everyone read permission disabled, mod role read and manage permissions enabled, and added member read permission enabled
		* Result: PASS
### **on_raw_message_delete**
	* Cached, bot
		* Expected: no log
		* Result: PASS
	* Cached, not bot, no attachments, text only
		* Expected: log with deleted message
		* Result: PASS
	* Cached, not bot, single image
		* Expected: log with image in embed OR "unable to save attachment" message
		* Result: PASS (may vary)
	* Cached, not bot, multiple images
		* Expected: log with all images in embed OR "unable to save attachment" message
		* Result: PASS (may vary)
	* Cached, not bot, single supported non-image attachment
		* Expected: log with attachment message followup OR "unable to save attachment" message
		* Result: PASS (may vary)
	* Cached, not bot, multiple supported non-image attachments
		* Expected: log with multi-attachment message followup OR "unable to save attachment" message
		* Result: PASS (may vary)
	* Cached, not bot, mix of images and non-image attachments
		* Expected: log with images in embed and multi-attachment message followup
		* Result: PASS (may vary)
	* Cached, not bot, single unsupported attachment
		* Expected: log with "unable to save attachment" message
		* Result: PASS
	* Cached, not bot, multiple unsupported attachments
		* Expected: log with "unable to save attachment" message
		* Result: PASS
	* Uncached, bot
		* Expected: log with uncached message description
		* Result: PASS
	* Uncached, not bot
		* Expected: log with uncached message description
		* Result: PASS
### **on_raw_message_edit**
	* Cached, bot
		* Expected: no log
		* Result: PASS
	* Cached, not bot, text<1000 characters
		* Expected: log with full-length message (before+after)
		* Result: PASS
	* Cached, not bot, text>1000 characters
		* Expected: log with truncated message (before+after)
		* Result: PASS
	* Cached, not bot, embed/upload edit
		* Expected: no log
		* Result: PASS
	* Uncached, bot
		* Expected: no log
		* Result: PASS
	* Uncached, not bot, text<1000 characters
		* Expected: log with full-length message (after only)
		* Result: PASS
	* Uncached, not bot, text>1000 characters
		* Expected: log with truncated message (after only)
		* Result: PASS
### remove_duplicate_welcomes
	* Expected: deletes duplicate messages from the same author in the welcome channel by searching the last 5 messages (ignores Discord Nitro boost messages)
	* Result: PASS - only tested on non-Nitro messages

	* Uncached, not bot, embed/upload edit
		* Expected: log with full-length message (after only)
		* Result: PASS
### **restrict**
	* No channel creation
		* Expected: no channels visible
		* Result: PASS
	* Create channel, no message
		* Expected: no channels visible except ticket channel, no message sent
		* Result: PASS
	* Create channel, default message
		* Expected: no channels visible except ticket channel, default message sent
		* Result: PASS
	* Create channel, custom message
		* Expected: no channels visible except ticket channel, custom message sent
		* Result: PASS
### **save_transcript**
	* Owner not specified (None)
		* Expected: transcript created and sent to transcript channel
		* Result: PASS
	* Owner specified
		* Expected: transcript created and sent to transcript channel; embed includes owner member information
		* Result: PASS
### **translate**
	* Target language DE
		* Expected: translation to German
		* Result: PASS
	* Target language EN-US
		* Expected: translation to English
		* Result: PASS
	* Target language ZH
		* Expected: translation to Chinese
		* Result: PASS
### **unrestrict**
	* No ticket channel deletion
		* Expected: channel visibility restored, ticket channel persists
		* Result: PASS
	* Ticket channel deletion
		* Expected: channel visibility restored, ticket channel deleted and transcript sent to log channel
		* Result: PASS

