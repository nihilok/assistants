from assistants.cli.commands import COMMAND_MAP


def generate_help_text() -> str:
    """
    Generate the help text for the commands.

    :return: The help text for the commands with commands sharing the same help grouped together.
    """
    # Group commands by their help text
    help_to_commands: dict[str, list[str]] = {}
    for command, cmd in COMMAND_MAP.items():
        if cmd.help in help_to_commands:
            help_to_commands[cmd.help].append(command)
        else:
            help_to_commands[cmd.help] = [command]

    # Prepare command groups and determine max width
    command_groups = []
    for help_text, commands in help_to_commands.items():
        commands.sort(key=len)  # Sort by length to put short commands first
        # Find the first non-None ARG_STRING among the commands in this group
        arg_string = None
        for c in commands:
            cmd_obj = COMMAND_MAP[c]
            if hasattr(cmd_obj, "ARG_STRING") and cmd_obj.ARG_STRING:
                arg_string = cmd_obj.ARG_STRING
                break
        command_group = ", ".join(commands)
        if arg_string:
            command_group = f"{command_group} {arg_string}"
        command_groups.append((command_group, help_text))
    if command_groups:
        max_command_width = max(len(group) for group, _ in command_groups)
    else:
        max_command_width = 0
    padding = 4  # spaces between columns

    # Format each entry with aligned columns
    formatted_lines = []
    for command_group, help_text in sorted(command_groups, key=lambda x: x[0]):
        formatted_lines.append(
            f"{command_group.ljust(max_command_width + padding)}{help_text}"
        )

    return (
        "\n".join(formatted_lines)
        + "\nCTRL+L to clear the screen\nCTRL+C to cancel command\nCTRL+D to exit"
    )
