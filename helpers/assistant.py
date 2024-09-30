import openai
from tinygen.helpers.environment import getenv

# OpenAI configuration
# TODO: May consider moving this configuration to a configuration method on the api service instead since configuration should be unique to a service i.e. the service decides who it
# talks to. Well this is debatable but it's probably less confusing to just have all the configuration in one place.
openai.api_key = getenv("OPENAI_API_KEY")

# Arbitrarily set the length of the chat history to 10 messages since this isn't important right now
CHAT_CONTEXT_MESSAGE_LIMIT = 10


class Assistant:
    __openai_client = openai.OpenAI()

    def __init__(self):
        self.chat_history = []

    def chat(self, prompt: str) -> str:
        # Crudely cap the chat context to a predefined number of messages
        if (len(self.chat_history)) == CHAT_CONTEXT_MESSAGE_LIMIT:
            self.chat_history.pop(0)

        self.chat_history.append({"role": "user", "content": prompt})

        response = Assistant.__openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=self.chat_history
        )

        assistant_message = response.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def delete_chat_history(self):
        self.chat_history = []
