ReadOnlyBot
===========

This Telegram bot helps you to administrate Telegram groups.

There are few functions in this bot at the moment:

1. Read only mode.
2. Fast answering by commands.
3. Welcome new members.
4. Ban users
5. Mute users

In first mode bot deletes all messages in the group (except messages from adminstrators and creator).

Second mode helps to quick answer to other user by declared commands. 

Third helps to inform new members with some information.

Built-in commands
--

> /add \</command> \<answerMessage>

add declared command with answer messge

> /update \</command> \<answerMessage>

update declared command with answer message

> /delete \</command>

delete declared command

>/getcommands

get list of declared commands. List will be send to user which call bot

>/startRO \<additionalMessage>

start read only mode and send additional message to chat (if given)

>/stopRO \<additionalMessage>

stop read only mode and send additional message to chat (if given)

>/setwelcomemessage \<welcomeMessage>

set message which will be send to chat when new member enter to chat. Use {$name} to set where user first name will be stand in message. Welcome message will be deleted (if bot have rights to do it) in 30 seconds.

>/ban \<reason>

ban user in this chat. Ban reason will be saved to the database. 

>/mute \<reason>

mute user in this chat. Mute reason will be save to the database.

**NOTE:** all commands except declared and /getcommands available only to admins or creator. Also all commands with bot and declared commands will be deleted.

Requirements
--

Bot requires Python 3 with telegram-python-bot, SQLAlchemy and simplejson packages installed. Also deleting messages requires disabled privacy mode in telegram and permission to delete messages in chat.

Configuration
--

To use this bot you should set bot token applied by @BotFather in btConfig.py

All commands should be send to chat that commands you want to setup