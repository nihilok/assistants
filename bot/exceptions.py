class BotException(Exception):
    pass


class ConfigError(BotException):
    pass


class NoResponseError(BotException):
    pass
