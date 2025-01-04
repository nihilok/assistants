from setuptools import find_packages, setup

setup(
    name="assistants",
    version="0.1.0",
    author="Michael Jarvis",
    author_email="nihilok@jarv.dev",
    description="OpenAI Assistants Framework and CLI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/nihilok/assistants",
    packages=find_packages(),
    install_requires=[
        "openai==1.59.3",
        "python-telegram-bot==21.10",
        "aiosqlite==0.20.0",
        "loguru==0.7.3",
        "pyperclip==1.9.0",
        "pytest==8.3.4",
        "requests==2.32.3",
        "prompt-toolkit==3.0.48",
        "pygments==2.18.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "ai-cli=main:main",
            "run-tg-bot=main_tg:main",
        ],
    },
    python_requires=">=3.10",
)
