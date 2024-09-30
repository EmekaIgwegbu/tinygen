import openai

# Arbitrarily set the length of the chat history to 10 messages since this isn't important right now
CHAT_CONTEXT_MESSAGE_LIMIT = 10


class Assistant:
    def __init__(self):
        self.__openai_client = openai.OpenAI()
        self.chat_history = []

    def chat(self, prompt: str) -> str:
        # Crudely cap the chat context to a predefined number of messages
        if (len(self.chat_history)) == CHAT_CONTEXT_MESSAGE_LIMIT:
            self.chat_history.pop(0)

        self.chat_history.append({"role": "user", "content": prompt})

        response = self.__openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=self.chat_history
        )

        assistant_message = response.choices[0].message.content
        self.chat_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def delete_chat_history(self):
        self.chat_history = []
