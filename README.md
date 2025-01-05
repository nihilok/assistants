# Assistants Framework

Welcome to the AI Assistants Framework! This repository contains the foundational code for creating versatile AI assistants capable of interacting through various front-end interfaces and utilizing interchangeable data layers. The goal is to create a powerful yet flexible assistants framework that can adapt to different user needs and environments.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Front-End Support**: The AI assistant (configured via environment variables) can interact through different user interfaces, including CLI and Telegram.
- **Interchangeable Data Layers**: Easily swap out the underlying data storage solutions, such as SQLite or other databases (coming soon).
- **Extensible Architecture**: Built with modularity in mind, allowing for easy addition of new features and integrations.
- **User Data Management**: Efficient handling of user data with a robust backend.

## Installation

To get started with the AI Assistant Project, follow these steps:

- Create a Python virtual environment (recommended, but not required on most systems) (Requires Python 3.10+)

(a simple way is to use the built-in `venv` module, e.g., `python -m venv my-venv; source my-venv/bin/activate`)

- Install the package using pip:

```bash
pip install assistants-framework
```

You can then run the following command to start the CLI:

```bash
$ ai-cli
```

NOTE: if your virtual environment is not activated, you may need to use /path/to/venv/bin/ai-cli instead of just ai-cli. Consider adding the virtual environment's bin directory to your PATH or otherwise linking the executable to a location in your PATH or creating an alias.

If you wish to use the Telegram bot interface, you can install the additional dependencies:

```bash
pip install assistants-framework[telegram]
```

## Usage

### Command Line Interface

For help running the assistant through the CLI, simply run:

```
$ ai-cli --help
usage: ai-cli [-h] [-e] [-f INPUT_FILE] [-i INSTRUCTIONS_FILE] [-t] [-C] [prompt ...]

CLI for AI Assistant

positional arguments:
  prompt                Positional arguments concatenate into a single prompt. E.g. `ai-cli
                        Is this a single prompt\?` (question mark escaped) ...will be passed
                        to the program as a single string (without the backslash). You can
                        also use quotes to pass a single argument with spaces and special
                        characters. See the -e and -f options for more advanced prompt
                        options.

options:
  -h, --help            show this help message and exit
  -e, --editor          Open the default editor to compose a prompt.
  -f INPUT_FILE, --input-file INPUT_FILE
                        Read the initial prompt from a file (e.g., 'input.txt').
  -i INSTRUCTIONS_FILE, --instructions INSTRUCTIONS_FILE
                        Read the initial instructions (system message) from a specified
                        file; if not provided, environment variable `ASSISTANT_INSTRUCTIONS`
                        or defaults will be used.
  -t, --continue-thread
                        Continue previous thread. (not currently possible with `-C` option)
  -C, --code            Use specialised reasoning/code model. WARNING: This model will be
                        slower and more expensive to use.
```

```

### Telegram Bot

To run the telegram bot polling loop, you can just use the following command:

```bash
$ ai-tg-bot
```

You can customize the behavior of the assistant by modifying the `ASSISTANT_INSTRUCTIONS` environment variable, which defaults to `"You are a helpful assistant."`

## Environment Variables

In addition to `ASSISTANT_INSTRUCTIONS`, other environment variables that can be configured include:

- `ASSISTANTS_API_KEY_NAME` - The name of the API key environment variable to use for authentication (defaults to `OPENAI_API_KEY`) - remember to also set the corresponding API key value to the environment variable you choose (or the default).
- `DEFAULT_MODEL` - The default model to use for OpenAI API requests (defaults to `gpt-4o-mini`)
- `CODE_MODEL` - more advanced reasoning model to use for OpenAI API requests (defaults to `o1-mini`)
- `TG_BOT_TOKEN` - The Telegram bot token if using the Telegram UI

## Contributing

Contributions are welcome! If you have suggestions for improvements, please feel free to submit a pull request or open an issue.

1. Fork the repository.
2. Commit your changes.
3. Open a pull request.

See the dev dependencies in the dev_requirements.txt file for formatting and linting tools.

#### TODOS: 

- optional local threads API built on top of langchain
- add postgresql support for data layer
- add support for more models/APIs

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Thank you for checking out the AI Assistant Project! I hope you find it useful and inspiring. Check out some example conversations below to see the assistant in action.

---
```
>>> help
-h, --help:   Show this help message
-e:           Open the default editor to compose a prompt
-c:           Copy the previous response to the clipboard
-cb:          Copy the code blocks from the previous response to the clipboard
-n:           Start a new thread and clear the terminal screen
clear:        (or CTRL+L) Clear the terminal screen without starting a new thread

>>> What's the current time?
The current time is January 4, 2025, at 13:02:17.

>>> What's one of the most difficult words to define and why?
One of the most difficult words to define is "love." The complexity of love arises from several factors:

1. **Subjectivity**: Love is a deeply personal and subjective experience. Different people may have different interpretations and feelings associated with love, making a universal definition challenging.

2. **Multiple Forms**: Love encompasses various forms, including romantic love, platonic love, familial love, and self-love. Each type has its own nuances and characteristics, complicating any singular definition.

3. **Cultural Variations**: Cultural norms and societal values influence how love is expressed, experienced, and understood. What love means in one culture may differ drastically in another.

4. **Philosophical and Psychological Perspectives**: Philosophers, psychologists, and theologians have debated the nature of love for centuries, contributing a wide range of theories and definitions. This academic discourse adds layers of complexity to the term.

5. **Emotional Ambiguity**: Love can evoke a range of emotions, from joy to pain, making it difficult to encapsulate in a single definition.

6. **Evolving Nature**: Love can change over time in the context of relationships, making a static definition inadequate.

For these reasons, defining "love" can evoke a rich and complex discussion rather than a straightforward answer.

>>> Give me an example of a Rust impl Display
In Rust, the `std::fmt::Display` trait is used for formatting a type for user-facing output. When you implement the `Display` trait for a struct or enum, you must define a method called `fmt` that specifies how the type should be formatted.

Here’s a simple example of implementing the `Display` trait for a custom struct:

```rust
use std::fmt;

// Define a struct
struct Point {
    x: f64,
    y: f64,
}

// Implement the Display trait for the Point struct
impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Point({:.2}, {:.2})", self.x, self.y)
    }
}

fn main() {
    let point = Point { x: 3.5, y: 2.1 };
    println!("The point is: {}", point);
}
\`\`\`

### Explanation:

1. **Struct Definition**: The `Point` struct has two fields: `x` and `y`, representing coordinates.

2. **Implementing `Display`**: We use `impl fmt::Display for Point` to start implementing the trait. The `fmt` method takes a mutable reference to a `fmt::Formatter` and returns a `fmt::Result`.

3. **Formatting**: Inside the `fmt` method, we use `write!` macro to format the output. Here, we print the point's coordinates, rounded to two decimal places.

4. **Using `Point`**: In the `main` function, we create a `Point` instance and use `println!` to output a string that includes the `point`, which implicitly calls the `fmt` method of the `Display` trait.

This example demonstrates how to create a custom type and provide a user-friendly string representation of it using the `Display` trait in Rust.

>>>
```

---

```
>>> hi
Hello! How can I assist you today?

>>> What are your instructions?
I'm here to assist you with a variety of tasks, including:

- Answering questions and providing information on a wide range of topics.
- Assisting with problem-solving and offering explanations.
- Helping with programming and technical queries.
- Analyzing data or performing calculations.
- Offering insights and suggestions for projects or ideas.

If you have something specific in mind, feel free to ask!

>>>
>>> What kind of calculations can you perform?
I can perform a wide range of calculations, including but not limited to:

1. **Basic Arithmetic**: Addition, subtraction, multiplication, division.
2. **Statistics**: Mean, median, mode, standard deviation, variance.
3. **Algebra**: Solving equations, evaluating expressions.
4. **Geometry**: Area, perimeter, volume calculations.
5. **Calculus**: Derivatives, integrals (basic concepts).
6. **Financial Calculations**: Interest calculations, loan amortization, investment growth.
7. **Data Analysis**: Summarizing datasets, finding correlations, making plots.

If you have a specific calculation in mind, just let me know!

>>> Do you use your code interpreter tool to perform those?
```
Yes, I use a code interpreter tool to perform calculations and analyze data. This allows me to write and execute code, which can handle mathematical operations, data manipulation, and even generate visualizations. If you have a specific calculation or task in mind, I can use this tool to assist you. Just let me know what you need!
```
>>> If were to perform searches for information that you require, would you be able to calcula
te and plot the length vs nobbliness of twiglets?
```
I currently don't have the capability to perform online searches for real-time information. However, if you can provide me with the data regarding the length and nobbliness of Twiglets (or any other relevant details), I can certainly help you analyze it, perform calculations, and create plots based on what you provide.

Feel free to share the data or any other specific information you'd like to work with!
```
>>> Where should I look for such data?
To find data on the length and "nobbliness" of Twiglets (or similar snack products), you might consider the following sources:
```
1. **Food Blogs and Reviews**: Some blogs may include detailed reviews and characteristics of various snacks, including measurements.

2. **Manufacturer Information**: Check the official website of the brand that produces Twiglets. They may have specifications or nutritional information that includes dimensions.

3. **Consumer Surveys**: Websites like SurveyMonkey or Google Forms may host consumer surveys about snack products, although this data might not be readily available.

4. **Academic Research**: Search academic databases like Google Scholar for studies on snack characteristics. This could include texture analysis or consumer preference studies.

5. **Social Media**: Platforms like Instagram or TikTok where users review snacks may have user-generated content that includes dimensions and texture descriptions.

6. **Retail Websites**: Online shops that sell Twiglets might occasionally have detailed descriptions or customer reviews that give insights into product characteristics.
```
If you can gather some data from any of these sources, I can help you analyze and visualize it!

>>> What do you think my chances are of gathering significant/meaningful data are in this case
?
Gathering significant or meaningful data on the length and "nobbliness" of Twiglets can be challenging due to the following factors:
```
1. **Specificity of Data**: Information like "nobbliness" is subjective and not usually measured in standard product specifications. Gathering numerical data on this characteristic may require personal assessment or consumer input rather than official data.

2. **Availability of Research**: While there might be some product-related studies, dedicated research on specific snack attributes is relatively rare. Most available data on snacks tends to focus on nutritional information.

3. **Consumer Generated Content**: While social media may provide insight, the data can be scattered and may not be in a structured format, making it hard to analyze systematically.

4. **Sample Size**: If you can gather data from different users or sources, the sample size will influence the validity of the insights you can generate. A small sample may not be representative of the broader population's views or experiences.

5. **Quantitative vs. Qualitative**: If you obtain data, it might be more qualitative (opinions, descriptions) rather than quantitative (exact measurements), which can limit the types of analysis that can be performed.

### Conclusion
If you focus on what you can gather — perhaps a combination of personal measurements, social media feedback, and any available consumer reviews — you might still be able to create an interesting, albeit limited, dataset. Collecting qualitative insights could also lead to informative discussions or presentations even if numerical data is scarce.
```
If you identify some data points, I'll be glad to help you analyze them!

>>> -c
Copied response to clipboard

>>>
```