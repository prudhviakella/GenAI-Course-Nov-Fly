"""
OpenAI API Parameters Explained With Practical Examples

This document explains the most important parameters when calling OpenAI APIs.
Each parameter is explained in plain language with real-world examples to help
you understand when and how to use them.

You do not need technical background in statistics or machine learning to
understand this guide. Everything is explained using everyday analogies.

--------------------------------------------------------------------------------
PARAMETER: model
--------------------------------------------------------------------------------

What it does:
Selects which AI "brain" will process your request. Different models have
different capabilities, speeds, and costs.

Think of it like choosing a vehicle:
- A sports car (gpt-4o) is fast and powerful but expensive
- A family sedan (gpt-4o-mini) is economical and reliable
- A truck (gpt-4-turbo) handles heavy-duty tasks

Available models and when to use them:

gpt-4o (Latest flagship model)
- Best for: Complex reasoning, nuanced understanding, high-quality writing
- Speed: Fast
- Cost: Higher
- Use when: Quality matters more than cost
- Example: Writing legal documents, complex analysis, creative content

gpt-4o-mini (Efficient model)
- Best for: Simple tasks, high-volume processing, chat applications
- Speed: Very fast
- Cost: Lower (about 60% cheaper than gpt-4o)
- Use when: Cost and speed matter, task is straightforward
- Example: Classification, simple Q&A, data extraction

gpt-4-turbo (Previous generation)
- Best for: Large context windows, detailed analysis
- Speed: Moderate
- Cost: Moderate
- Use when: You need to process very long documents
- Example: Analyzing 50-page reports, book summaries

How to choose:
- Start with gpt-4o-mini for testing
- Upgrade to gpt-4o if quality is not good enough
- Use gpt-4-turbo only if you need extra-long context

Code example:
model = "gpt-4o"           # High quality
model = "gpt-4o-mini"      # Cost effective
model = "gpt-4-turbo"      # Large documents

--------------------------------------------------------------------------------
PARAMETER: temperature
--------------------------------------------------------------------------------

What it does:
Controls how predictable vs creative the AI's responses are.

Real-world analogy:
Imagine you ask 3 chefs to make scrambled eggs.

Temperature = 0.0 (No creativity)
- All 3 chefs follow the exact same recipe
- Every plate looks identical
- Predictable, consistent, boring

Temperature = 0.7 (Some creativity)
- Chef 1 adds cheese
- Chef 2 adds herbs
- Chef 3 makes it plain
- Similar but with variations

Temperature = 1.5 (Lots of creativity)
- Chef 1 makes a soufflé
- Chef 2 makes eggs benedict
- Chef 3 makes a frittata
- Very different interpretations

How temperature affects AI responses:

Low Temperature (0.0 - 0.3):
- AI gives the same answer every time
- Very focused and deterministic
- Picks the most likely words
- Best for factual tasks

Medium Temperature (0.4 - 0.8):
- AI gives similar but varied answers
- Balanced between consistency and variety
- Some creativity allowed
- Best for general-purpose tasks

High Temperature (0.9 - 2.0):
- AI gives very different answers each time
- More experimental and creative
- Can be unpredictable or even strange
- Best for brainstorming and creative writing

When to use different temperatures:

Temperature 0.0:
- Classification: "Is this email spam or not spam?"
- Data extraction: "Extract the order number from this text"
- Math problems: "What is 15% of 200?"
- Code generation: "Write a function to sort a list"

Temperature 0.3:
- Factual explanations: "Explain how photosynthesis works"
- Summarization: "Summarize this article in 3 sentences"
- Technical documentation: "Document this API endpoint"

Temperature 0.7 (Default):
- General Q&A: "What are the benefits of exercise?"
- Product descriptions: "Describe this coffee maker"
- Email responses: "Write a professional email to a client"

Temperature 1.0:
- Creative writing: "Write a short story about a robot"
- Marketing copy: "Create 5 taglines for our product"
- Brainstorming: "Give me 10 unique business ideas"

Temperature 1.5+:
- Poetry and artistic content
- Experimental or surreal writing
- Multiple alternative perspectives

Important notes:
- You can run the same prompt multiple times with high temperature
  to get different ideas
- Lower temperature saves money (fewer tokens wasted on variety)
- For production systems, use 0.0-0.3 for consistency

Code example:
temperature = 0.0    # Classification, extraction
temperature = 0.3    # Factual tasks
temperature = 0.7    # General purpose
temperature = 1.0    # Creative tasks

--------------------------------------------------------------------------------
PARAMETER: max_tokens
--------------------------------------------------------------------------------

What it does:
Sets the maximum length of the AI's response.

Think of it like a word limit on an essay:
- max_tokens = 50 means "answer in one short paragraph"
- max_tokens = 500 means "write a detailed explanation"
- max_tokens = 2000 means "write a comprehensive analysis"

What is a token?
A token is approximately 4 characters or 0.75 words in English.

Quick conversion guide:
- 100 tokens = about 75 words = 1 short paragraph
- 500 tokens = about 375 words = 1-2 paragraphs
- 1000 tokens = about 750 words = 1 page
- 2000 tokens = about 1500 words = 2-3 pages

When to use different max_tokens values:

Small (50-100 tokens):
- One-word or one-sentence answers
- Classifications
- Short confirmations
Example: "Classify this as positive or negative"

Medium (200-500 tokens):
- Summaries
- Brief explanations
- Email responses
Example: "Summarize this article"

Large (1000-2000 tokens):
- Detailed explanations
- Long-form content
- Code with documentation
Example: "Explain quantum computing with examples"

Very Large (2000+ tokens):
- Essays
- Multiple examples
- Comprehensive guides
Example: "Write a tutorial on Python functions"

Important considerations:

Cost implications:
- You pay for both input tokens (your prompt) and output tokens (AI response)
- Setting max_tokens too high wastes money
- Set it just above what you actually need

Quality implications:
- If max_tokens is too small, the response will be cut off mid-sentence
- The AI will try to fit everything into the limit
- Better to set it slightly higher than needed

How to choose the right value:
1. Estimate how long the answer should be
2. Convert to tokens (words × 1.3)
3. Add 20% buffer
4. Round up to a clean number

Examples:

Task: Extract email address
Expected output: 1 line
max_tokens = 50

Task: Product description
Expected output: 2-3 paragraphs
max_tokens = 300

Task: Blog post
Expected output: 5-6 paragraphs
max_tokens = 1500

Code example:
max_tokens = 50      # One-line answers
max_tokens = 200     # Short paragraphs
max_tokens = 1000    # Detailed responses
max_tokens = 2000    # Long-form content

--------------------------------------------------------------------------------
PARAMETER: messages
--------------------------------------------------------------------------------

What it does:
Represents the entire conversation history between you and the AI.
The AI does not remember past conversations on its own. You must include
all relevant context in the messages array.

Think of it like showing someone a text message thread:
- They can only see what you show them
- If you show them just the last message, they lack context
- If you show the full thread, they understand the conversation

Message structure:
Each message has two parts:
1. role: Who is speaking (system, user, or assistant)
2. content: What they said

The three roles explained:

ROLE: system
- Sets the behavior, personality, or rules for the AI
- Like giving someone a job description before they start work
- The AI follows these instructions throughout the conversation
- Only needed once at the start

Example system messages:
"You are a helpful customer service agent for a tech company."
"You are a professional medical assistant. Always ask for clarification
if symptoms are unclear."
"You are a creative writing coach who gives constructive feedback."

ROLE: user
- Represents the human asking questions or giving instructions
- This is what you want the AI to respond to
- Can be a question, request, or statement

Example user messages:
"What is machine learning?"
"Write a product description for a coffee maker"
"Classify this email as spam or not spam"

ROLE: assistant
- Represents previous AI responses
- Used when you want to continue a conversation
- The AI remembers what it said before

Example assistant messages:
"Machine learning is a type of artificial intelligence..."
"Here's a product description: This premium coffee maker..."

How messages work in practice:

Single-turn conversation (one question, one answer):
[
    {"role": "user", "content": "What is Python?"}
]

With system prompt (setting behavior):
[
    {"role": "system", "content": "You are a programming teacher."},
    {"role": "user", "content": "What is Python?"}
]

Multi-turn conversation (remembering context):
[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "What is the population?"}
]

Notice how the AI can understand "What is the population?" refers to Paris
because we included the previous exchange.

Real-world example: Appointment booking system

Turn 1:
[
    {"role": "system", "content": "You are an appointment scheduler."},
    {"role": "user", "content": "I need a doctor appointment."}
]
AI responds: "What type of doctor do you need to see?"

Turn 2 (adding AI's response and user's reply):
[
    {"role": "system", "content": "You are an appointment scheduler."},
    {"role": "user", "content": "I need a doctor appointment."},
    {"role": "assistant", "content": "What type of doctor do you need to see?"},
    {"role": "user", "content": "I need a dentist."}
]
AI responds: "What day works best for you?"

Turn 3 (continuing the conversation):
[
    {"role": "system", "content": "You are an appointment scheduler."},
    {"role": "user", "content": "I need a doctor appointment."},
    {"role": "assistant", "content": "What type of doctor do you need to see?"},
    {"role": "user", "content": "I need a dentist."},
    {"role": "assistant", "content": "What day works best for you?"},
    {"role": "user", "content": "Thursday afternoon."}
]

Important notes:
- Always include the system message at the start
- Include all previous turns for context
- The AI has no memory beyond what you send
- Longer message history = more tokens = higher cost

Best practices:
- For simple tasks, just send user message
- For consistent behavior, add system message
- For conversations, include full history
- Trim old messages if conversation gets too long (keep last 5-10 turns)

Code example:
# Simple question
messages = [
    {"role": "user", "content": "What is AI?"}
]

# With system prompt
messages = [
    {"role": "system", "content": "You are a teacher."},
    {"role": "user", "content": "What is AI?"}
]

# Conversation
messages = [
    {"role": "system", "content": "You are a teacher."},
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI stands for..."},
    {"role": "user", "content": "Give me an example."}
]

--------------------------------------------------------------------------------
PARAMETER: top_p (nucleus sampling)
--------------------------------------------------------------------------------

What it does:
Controls which words the AI is allowed to consider when generating the
next word in its response.

Think of it like a restaurant menu filtering system:

The AI has a mental list of possible next words, ranked by how likely
they are to make sense. Some words are very likely, some are unlikely.

top_p = 1.0 (Full menu)
- AI sees all possible words, even weird ones
- Like seeing every item on the menu including secret items

top_p = 0.9 (Recommended items)
- AI only sees the most sensible words that cover 90% of good options
- Like filtering menu to show "customer favorites"

top_p = 0.5 (Best sellers only)
- AI only sees the very most likely words
- Like showing only the top 10 most popular dishes

Real-world example:

Sentence so far: "The cat sat on the..."

If top_p = 1.0, AI might consider:
- mat (very likely)
- chair (likely)
- roof (possible)
- table (possible)
- spaceship (unlikely but allowed)
- quantum-entangled particle accelerator (extremely unlikely but allowed)

If top_p = 0.9, AI considers:
- mat
- chair
- roof
- table
(Filters out the weird options)

If top_p = 0.5, AI considers:
- mat
- chair
(Only the most obvious options)

When to use different top_p values:

top_p = 0.9 (Default, recommended):
- Balanced responses
- Filters out nonsense while allowing some creativity
- Good for almost all use cases

top_p = 1.0 (Maximum freedom):
- Creative writing
- Brainstorming
- Generating many alternative ideas

top_p = 0.5 (Very focused):
- Technical documentation
- Formal writing
- When you want conservative, safe responses

Important note:
top_p and temperature work together. You typically adjust temperature
and leave top_p at the default (0.9). Only adjust top_p if you have
a specific reason.

Relationship between temperature and top_p:
- temperature controls randomness
- top_p controls the pool of words to pick from
- Both together determine creativity

Most common combinations:
temperature = 0.0, top_p = 0.9  (Factual tasks)
temperature = 0.7, top_p = 0.9  (General purpose)
temperature = 1.0, top_p = 1.0  (Maximum creativity)

Code example:
top_p = 0.9    # Default, recommended for most tasks
top_p = 1.0    # Creative tasks
top_p = 0.5    # Very conservative responses

--------------------------------------------------------------------------------
PARAMETER: frequency_penalty
--------------------------------------------------------------------------------

What it does:
Reduces how often the AI repeats the same words or phrases.

Think of it like a conversation rule:

frequency_penalty = 0.0
- No penalty for repetition
- AI can say the same thing over and over
- Like a speaker who uses the same phrase repeatedly

frequency_penalty = 0.5
- Mild penalty for repetition
- AI tries to vary its language
- Like reminding someone "you already said that"

frequency_penalty = 1.0
- Strong penalty for repetition
- AI actively avoids any repeated words
- Like being told "use a different word every time"

Real-world example:

Without penalty (frequency_penalty = 0.0):
"Python is great. Python is versatile. Python is powerful. Python is
easy to learn. I really like Python."

With mild penalty (frequency_penalty = 0.5):
"Python is great. It's versatile and powerful. The language is easy to
learn. I really like it."

With strong penalty (frequency_penalty = 1.0):
"Python is great. The language offers versatility and strength. Learning
this programming tool proves straightforward. I genuinely enjoy coding
with it."

When to use different values:

frequency_penalty = 0.0 (No penalty):
- Short responses where repetition is acceptable
- Technical terms that need to be repeated
- Code generation

frequency_penalty = 0.3-0.5 (Mild penalty):
- General writing
- Marketing copy
- Email responses
- Product descriptions

frequency_penalty = 0.8-1.0 (Strong penalty):
- Creative writing
- Long-form content
- When variety is important
- Lists with diverse items

Problems with setting it too high:
- AI might use awkward synonyms
- Can sound unnatural
- May avoid technical terms that should be repeated

Best practice:
Start with 0.0 and only increase if you notice excessive repetition.

Code example:
frequency_penalty = 0.0    # Allow repetition
frequency_penalty = 0.5    # Reduce repetition
frequency_penalty = 1.0    # Strongly avoid repetition

--------------------------------------------------------------------------------
PARAMETER: presence_penalty
--------------------------------------------------------------------------------

What it does:
Encourages the AI to talk about new topics instead of staying focused
on the same topic.

Think of it like a conversation coach:

presence_penalty = 0.0
- AI stays on topic
- Deep dive into one subject
- Like a focused discussion

presence_penalty = 0.6
- AI introduces related topics
- Brings in new angles
- Like a conversation that naturally branches out

presence_penalty = 1.0
- AI actively seeks new topics
- Explores different directions
- Like someone who keeps changing the subject

Real-world example:

Prompt: "Tell me about electric cars."

With presence_penalty = 0.0:
"Electric cars use battery power. The batteries store electricity.
Battery charging takes several hours. Battery technology is improving.
Battery costs are decreasing."
(Stays focused on batteries)

With presence_penalty = 0.6:
"Electric cars use battery power to drive motors. This reduces emissions
compared to gasoline vehicles. Charging infrastructure is expanding in
many cities. Government incentives make them more affordable."
(Introduces related concepts)

With presence_penalty = 1.0:
"Electric cars represent a shift in transportation. Urban planning must
adapt to charging needs. Renewable energy generation ties into this trend.
Economic impacts affect auto industry jobs. Cultural attitudes toward
sustainability influence adoption."
(Explores many angles)

When to use different values:

presence_penalty = 0.0 (Stay focused):
- Technical explanations
- Step-by-step instructions
- Focused analysis
- When depth matters more than breadth

presence_penalty = 0.3-0.6 (Balanced):
- General writing
- Explanatory content
- Blog posts
- Discussions that benefit from context

presence_penalty = 0.8-1.0 (Explore broadly):
- Brainstorming
- Ideation
- Exploring multiple perspectives
- Creative writing with varied scenes

Difference from frequency_penalty:
- frequency_penalty: "Don't repeat the same WORDS"
- presence_penalty: "Don't stay on the same TOPIC"

You can use both together:
- frequency_penalty reduces word repetition
- presence_penalty encourages topic variety

Code example:
presence_penalty = 0.0    # Stay focused on main topic
presence_penalty = 0.6    # Introduce related ideas
presence_penalty = 1.0    # Explore diverse topics

--------------------------------------------------------------------------------
PARAMETER: response_format
--------------------------------------------------------------------------------

What it does:
Forces the AI to return output in a specific structured format like JSON.

Think of it like choosing how you want your data delivered:

Normal response (no format specified):
- AI responds in natural language
- Good for humans to read
- Hard for programs to parse

JSON response (response_format specified):
- AI responds in structured data
- Easy for programs to parse
- Can be directly used in code

When to use response_format:

You should use JSON format when:
- Another program will read the response
- You need consistent structure
- You're building an API
- You need to extract specific fields

You should use natural text when:
- A human will read the response
- Flexibility is needed
- You want conversational output

Real-world example:

Prompt: "Analyze this product review: 'Great quality but expensive'"

Without response_format (natural text):
"This review is mixed. The customer appreciates the quality but has
concerns about the price. Overall sentiment is neutral to positive."

With response_format = {"type": "json_object"}:
{
    "sentiment": "MIXED",
    "positive_aspects": ["quality"],
    "negative_aspects": ["price"],
    "overall_rating": 3.5,
    "recommendation": "Good product if budget allows"
}

How to use it:

Step 1: Tell the AI to return JSON in your prompt
Prompt: "Analyze this review and return JSON with sentiment,
positive_aspects, negative_aspects."

Step 2: Set response_format parameter
response_format = {"type": "json_object"}

Step 3: Parse the JSON in your code
import json
result = json.loads(response_text)
sentiment = result["sentiment"]

Important rules when using JSON mode:

1. Always mention "JSON" in your prompt
Bad:  "Analyze this review"
Good: "Analyze this review and return JSON"

2. Specify the structure you want
"Return JSON with fields: sentiment, score, summary"

3. The AI will only return valid JSON
No explanations before or after
No markdown code blocks
Just pure JSON

4. Parse the response properly in your code
Use json.loads() in Python
Handle parsing errors

Common use cases for JSON format:

Classification tasks:
Input: "Classify this email"
Output: {"category": "SPAM", "confidence": 0.95}

Data extraction:
Input: "Extract order details"
Output: {"order_id": "12345", "amount": 99.99, "date": "2024-01-15"}

Structured analysis:
Input: "Analyze customer feedback"
Output: {
    "sentiment": "POSITIVE",
    "themes": ["quality", "service"],
    "issues": [],
    "score": 4.5
}

Multiple items:
Input: "List 3 product recommendations"
Output: {
    "recommendations": [
        {"name": "Product A", "price": 29.99, "reason": "Best value"},
        {"name": "Product B", "price": 49.99, "reason": "Premium quality"},
        {"name": "Product C", "price": 19.99, "reason": "Budget friendly"}
    ]
}

Code example:
# For human-readable responses
response_format = None  (or omit the parameter)

# For machine-readable structured data
response_format = {"type": "json_object"}

--------------------------------------------------------------------------------
PARAMETER: stream
--------------------------------------------------------------------------------

What it does:
Controls whether you get the AI's response all at once or piece by piece
as it's being generated.

Think of it like downloading a video:

stream = False (Download first, then watch):
- Wait for complete response
- Then display it all at once
- Like buffering the entire video before playing

stream = True (Watch while downloading):
- Get response in small chunks as it's generated
- Display each chunk immediately
- Like streaming video that plays while downloading

Visual comparison:

Without streaming (stream = False):
User waits...
User waits...
User waits...
Complete response appears: "Here is a detailed explanation of machine
learning including supervised learning, unsupervised learning, and
reinforcement learning."

With streaming (stream = True):
"Here"
"is"
"a detailed"
"explanation"
"of machine"
"learning"
(Words appear progressively, like someone typing)

When to use stream = True:

Good for:
- Chat applications (like ChatGPT interface)
- Real-time user interfaces
- Long responses where users want to start reading immediately
- When user experience matters more than code simplicity

Example: Customer service chatbot
User sees response appearing word by word, feels more interactive

When to use stream = False:

Good for:
- Batch processing
- APIs that return complete results
- When you need the full response to process it
- Simpler code

Example: Analyzing 100 reviews overnight
You don't need to see each response appear, just get all results

How streaming works technically:

Without streaming:
request → wait → receive complete response → process

With streaming:
request → receive chunk 1 → display
       → receive chunk 2 → display
       → receive chunk 3 → display
       → receive chunk 4 → display
       (continues until complete)

Code example for streaming:

Without streaming:
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain AI"}],
    stream=False
)
print(response.choices[0].message.content)

With streaming:
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain AI"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')

Important notes:
- Streaming is slightly more complex to code
- Streaming provides better user experience
- Non-streaming is easier for beginners
- Choose based on your application needs

Real-world scenarios:

Scenario 1: Interactive chatbot
Use stream = True
Why: Users want to see responses appearing in real-time

Scenario 2: Automated report generation
Use stream = False
Why: The program needs the complete result to save to a file

Scenario 3: Code generation tool
Use stream = True
Why: Developers like seeing code appear line by line

Scenario 4: Batch data processing
Use stream = False
Why: Processing 1000 items overnight, no one is watching

Code example:
stream = False    # Get complete response at once
stream = True     # Get response in chunks as generated

--------------------------------------------------------------------------------
QUICK REFERENCE GUIDE
--------------------------------------------------------------------------------

For beginners, use these defaults:

model = "gpt-4o-mini"           # Cost effective
temperature = 0.7                # Balanced
max_tokens = 1000                # Moderate length
top_p = 0.9                      # Default
frequency_penalty = 0.0          # No penalty
presence_penalty = 0.0           # Stay focused
response_format = None           # Natural text
stream = False                   # Simpler code

For classification and extraction:

model = "gpt-4o-mini"
temperature = 0.0
max_tokens = 200
response_format = {"type": "json_object"}

For creative writing:

model = "gpt-4o"
temperature = 1.0
max_tokens = 2000
frequency_penalty = 0.5
presence_penalty = 0.6

For chat applications:

model = "gpt-4o-mini"
temperature = 0.7
stream = True

Remember: Start simple, then adjust based on results.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_ai(
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 200,
        model: str = "gpt-4o"
) -> str:
    """
    Sends a prompt to OpenAI and returns the response with configurable parameters.

    This function demonstrates how different parameter values affect AI responses.
    Use this to experiment and understand parameter behavior.

    Parameters:
        prompt (str):
            The question or instruction you want the AI to respond to.
            Example: "Explain photosynthesis" or "Write a haiku about winter"

        temperature (float, default=0.7):
            Controls response creativity and randomness.
            Range: 0.0 to 2.0
            - 0.0 = Deterministic, same answer every time
            - 0.7 = Balanced, some variation
            - 1.5+ = Very creative, highly varied

        top_p (float, default=1.0):
            Controls diversity of word choices.
            Range: 0.0 to 1.0
            - 0.5 = Only most likely words
            - 0.9 = Recommended default
            - 1.0 = All possible words allowed

        max_tokens (int, default=200):
            Maximum length of response.
            Approximate guide:
            - 50 = One sentence
            - 200 = One paragraph
            - 500 = Multiple paragraphs
            - 1000 = Detailed explanation

        model (str, default="gpt-4o"):
            Which OpenAI model to use.
            - "gpt-4o" = Best quality, higher cost
            - "gpt-4o-mini" = Good quality, lower cost
            - "gpt-4-turbo" = Large context window

    Returns:
        str: The AI-generated response text

    Raises:
        Exception: If API key is missing or invalid
        Exception: If API call fails

    Example:
        response = ask_ai(
            "What is Python?",
            temperature=0.3,
            max_tokens=100
        )
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}\nPlease check your API key in .env file"


def run_comparison_examples():
    """
    Demonstrates how different parameter combinations affect responses.

    This function runs the same prompt with different parameter settings
    so you can see and compare the differences in AI behavior.
    """

    # The prompt we'll use for all examples
    test_prompt = "Explain artificial intelligence in simple terms."

    # Configuration for different scenarios
    examples = [
        {
            "name": "Conservative and Predictable",
            "description": "Low temperature for consistent, factual responses. Best for documentation.",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 150
        },
        {
            "name": "Balanced General Purpose",
            "description": "Default settings for everyday use. Good mix of accuracy and variety.",
            "temperature": 0.7,
            "top_p": 1.0,
            "max_tokens": 200
        },
        {
            "name": "Creative and Varied",
            "description": "Higher temperature for creative writing. Responses will be more unique.",
            "temperature": 1.2,
            "top_p": 1.0,
            "max_tokens": 250
        },
        {
            "name": "Concise and Focused",
            "description": "Short response with conservative parameters. Good for quick answers.",
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 75
        }
    ]

    print("\n" + "=" * 80)
    print("OpenAI Parameter Comparison Demo")
    print("=" * 80)
    print(f"\nPrompt used for all examples: \"{test_prompt}\"")
    print("\nWatch how the same prompt produces different responses with different settings.\n")

    # Run each example configuration
    for i, config in enumerate(examples, 1):
        print(f"\n{'-' * 80}")
        print(f"Example {i}: {config['name']}")
        print(f"{'-' * 80}")
        print(f"Description: {config['description']}")
        print(f"\nParameters:")
        print(f"  temperature  = {config['temperature']}")
        print(f"  top_p        = {config['top_p']}")
        print(f"  max_tokens   = {config['max_tokens']}")
        print(f"\nResponse:")
        print(f"{'-' * 80}")

        # Get AI response with these parameters
        response = ask_ai(
            test_prompt,
            temperature=config['temperature'],
            top_p=config['top_p'],
            max_tokens=config['max_tokens']
        )

        print(response)
        print()


def interactive_mode():
    """
    Interactive mode allowing you to experiment with parameters in real-time.

    This function lets you enter your own prompts and adjust parameters
    to see how they affect responses.
    """

    print("\n" + "=" * 80)
    print("Interactive Parameter Testing Mode")
    print("=" * 80)
    print("\nExperiment with different parameters to see how they affect responses.")
    print("Type 'quit' to exit.\n")

    while True:
        # Get user prompt
        user_prompt = input("Enter your prompt (or 'quit' to exit): ").strip()

        if user_prompt.lower() in ['quit', 'exit', 'q']:
            print("\nExiting interactive mode. Goodbye!")
            break

        if not user_prompt:
            print("Please enter a prompt.\n")
            continue

        # Get parameter values with defaults
        print("\nParameter settings (press Enter for defaults):")

        try:
            temp_input = input("  temperature (0.0-2.0, default=0.7): ").strip()
            temperature = float(temp_input) if temp_input else 0.7

            top_p_input = input("  top_p (0.0-1.0, default=1.0): ").strip()
            top_p = float(top_p_input) if top_p_input else 1.0

            tokens_input = input("  max_tokens (default=200): ").strip()
            max_tokens = int(tokens_input) if tokens_input else 200

        except ValueError:
            print("Invalid input. Using default values.")
            temperature = 0.7
            top_p = 1.0
            max_tokens = 200

        # Display what we're using
        print(f"\nUsing: temperature={temperature}, top_p={top_p}, max_tokens={max_tokens}")
        print(f"\nResponse:")
        print("-" * 80)

        # Get and display response
        response = ask_ai(
            user_prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )

        print(response)
        print("\n")


def demonstrate_use_cases():
    """
    Shows recommended parameter settings for common use cases.

    This function demonstrates optimal configurations for different
    types of tasks you might want to accomplish.
    """

    use_cases = [
        {
            "task": "Classification Task",
            "example_prompt": "Classify this review as POSITIVE or NEGATIVE: 'The product broke after one use.'",
            "temperature": 0.0,
            "top_p": 0.9,
            "max_tokens": 10,
            "explanation": "Use temperature=0 for consistent classifications. Same input always gives same output."
        },
        {
            "task": "Creative Writing",
            "example_prompt": "Write a creative opening sentence for a mystery novel.",
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 100,
            "explanation": "Higher temperature encourages creativity and variety in storytelling."
        },
        {
            "task": "Technical Documentation",
            "example_prompt": "Explain how to use Python's list comprehension.",
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 300,
            "explanation": "Low temperature ensures accurate, consistent technical information."
        },
        {
            "task": "Brainstorming Ideas",
            "example_prompt": "Give me 5 unique business ideas for a coffee shop.",
            "temperature": 1.2,
            "top_p": 1.0,
            "max_tokens": 400,
            "explanation": "High temperature generates diverse and unexpected ideas."
        }
    ]

    print("\n" + "=" * 80)
    print("Recommended Parameter Settings for Common Tasks")
    print("=" * 80)
    print("\nEach use case has optimal parameter settings for best results.\n")

    for i, use_case in enumerate(use_cases, 1):
        print(f"\n{'-' * 80}")
        print(f"Use Case {i}: {use_case['task']}")
        print(f"{'-' * 80}")
        print(f"Explanation: {use_case['explanation']}")
        print(f"\nExample prompt: \"{use_case['example_prompt']}\"")
        print(f"\nRecommended parameters:")
        print(f"  temperature  = {use_case['temperature']}")
        print(f"  top_p        = {use_case['top_p']}")
        print(f"  max_tokens   = {use_case['max_tokens']}")
        print(f"\nResponse:")
        print(f"{'-' * 80}")

        response = ask_ai(
            use_case['example_prompt'],
            temperature=use_case['temperature'],
            top_p=use_case['top_p'],
            max_tokens=use_case['max_tokens']
        )

        print(response)
        print()


if __name__ == "__main__":
    """
    Main program execution.

    Runs three different demonstration modes:
    1. Parameter comparison - See how settings affect the same prompt
    2. Use case examples - Optimal settings for different tasks
    3. Interactive mode - Experiment with your own prompts
    """

    print("\n" + "=" * 80)
    print("OpenAI Parameter Testing and Demonstration Tool")
    print("=" * 80)
    print("\nThis program helps you understand how OpenAI API parameters work.")
    print("You'll see practical examples and can experiment interactively.\n")

    # Run demonstrations
    try:
        # Part 1: Show how parameters change responses
        run_comparison_examples()

        input("\nPress Enter to continue to use case examples...")

        # Part 2: Show optimal settings for different tasks
        demonstrate_use_cases()

        input("\nPress Enter to start interactive mode...")

        # Part 3: Let user experiment
        interactive_mode()

    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting...")

    except Exception as e:
        print(f"\n\nAn error occurred: {str(e)}")
        print("Please check that your .env file contains a valid OPENAI_API_KEY")

    print("\n" + "=" * 80)
    print("Thank you for using the OpenAI Parameter Testing Tool")
    print("=" * 80)