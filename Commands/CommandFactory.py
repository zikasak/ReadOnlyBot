from Commands.CommandsImpl import AddCommand, DeleteCommand, DefaultCommand, UpdateCommand, GetCommandsCommand, \
    SetWelcomeMessage, BanUser, MuteUser, SetMuteTime, AddPhrase, DeletePhrase, GetPhrases


class CommandFactory:
    commands = {
        '/add': AddCommand,
        '/delete': DeleteCommand,
        '/update': UpdateCommand,
        '/getcommands': GetCommandsCommand,
        '/setwelcomemessage': SetWelcomeMessage,
        '/ban': BanUser,
        '/mute': MuteUser,
        '/mutetime': SetMuteTime,
        '/addPhrase': AddPhrase,
        '/deletePhrase': DeletePhrase,
        '/getPhrases': GetPhrases,
    }

    @staticmethod
    def get_command_handler(command, db_worker):
        try:
            res = CommandFactory.commands[command.strip()]
        except KeyError:
            return DefaultCommand(db_worker, command)
        return res(db_worker, command)
