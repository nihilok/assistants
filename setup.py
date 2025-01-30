from setuptools import find_packages, setup

from assistants import version

setup(
    name="assistants-framework",
    version=version.__VERSION__,
    author="Michael Jarvis",
    author_email="nihilok@jarv.dev",
    description="OpenAI Assistants Wrapper, with CLI and Telegram Bot",
    long_description=open("README.md").read() + "\n\n" + open("CHANGELOG.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nihilok/assistants",
    packages=find_packages(exclude=["assistants.tests*"]),
    install_requires=[
        "openai==1.59.3",
        "aiosqlite==0.20.0",
        "loguru==0.7.3",
        "pyperclip==1.9.0",
        "prompt-toolkit==3.0.48",
        "pygments==2.18.0",
        "anthropic==0.42.0",
        "aiofiles==24.1.0",
        "aiohttp==3.11.11",
    ],
    extras_require={
        "telegram": [
            # Dependencies for the Telegram bot integration
            "python-telegram-bot==21.10",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "ai-cli=assistants.main:main",
            "ai-tg-bot=assistants.main_tg:main",
            "claude=assistants.claude:main",
        ],
    },
    python_requires=">=3.10",
    keywords="openai gpt3 gpt3.5 gpt4 o1 chatgpt chatbot assistant assistants claude anthropic cli telegram llm bot ui tui coding-assistant coding programming",
)
