ReadOnlyBot
===========

This Telegram bot helps you to administrate Telegram groups.

There are two functions in this bot at the moment:

1. Read only mode.
2. Fast answering by commands
3. Welcome new members

In first mode bot deletes all messages in the group (except messages from adminstrators and creator).

Second mode helps to quick asnwer to other user by declared commands. Messages in which declared command used will be deleted.


Built-in commands
--

> /add \</command> \<answerMessage>

add declared command with answer messge

> /update \</command> \<answerMessage>

update declared command with answer message

> /delete \</command>

delete declared command

>/getcommands

get list of declared commands. List will be sended to user which call bot

>/startRO <additionalMessage>

start read only mode and send additional message to chat (if given)

>/stopRO <additionalMessage>

stop read only mode and send additional message to chat (if given)

>/setwelcomemessage \<welcomeMessage>

set message which will be sended to chat when new member enter to chat. Use {$name} to set where user first name will be stand in message. Welcome message will be deleted (if bot have rights to do it) in 30 seconds.

**NOTE:** all commands except declared and /getcommands available only to admins or creator

Requirements
--

Bot requires Python 3 with telegram-python-bot and SQLAlchemy packages installed. Also deleting messages requires disabled privacy mode in telegram and permission to delete messages in chat.

Configuration
--

To use this bot you should set bot token applied by @BotFather in btConfig.py

All commands should be sended to chat thar commands you want to setup