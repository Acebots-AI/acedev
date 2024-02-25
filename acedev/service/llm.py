from openai import OpenAI


class LLMService:

    def __init__(self, client: OpenAI):
        self.client = client

    def complete(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return completion.choices[0].message.content
