IO_INSTRUCTIONS = """\
Commands:

/h,  /help      Show this help message
/e,  /editor    Open the default editor to compose a prompt
/i,  /image <prompt>     
                Generate an image from the prompt supplied as args
                e.g. `/i a dog riding a pony, in the style of Botero`
/c,  /copy      Copy the previous response to the clipboard
/cc, /copy-code [i]
                Copy the code blocks from the previous response to the clipboard
                (an optional index can be supplied to copy a single code block)
/n,  /new       Start a new thread and clear the terminal screen
/t,  /threads:  List all the threads, and select one to continue
/clear, C-l     Clear the terminal screen without starting a new thread

Press Ctrl+C or Ctrl+D to exit the program

Anything else you type will be sent to the assistant for processing.\
"""

CLAUDE_CLI_MAX_TOKENS = 2048
