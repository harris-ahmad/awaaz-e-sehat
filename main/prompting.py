import re
from openai import OpenAI

CLIENT = OpenAI(api_key="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")

class Prompting:
    def __init__(self, file_path: str = '', transcription: str = None) -> None:
        self.file_path = file_path
        self.transcription = transcription
        self.messages = []

    def generate_messages(self) -> list:
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            content = content.encode('ascii', 'ignore').decode()
            if self.transcription:
                content = re.sub(
                    r'\[Transcription from Database\]', self.transcription,
                    content)

        # Define regex patterns for extracting system, user, and model prompts
        system_pattern = re.compile(r"System Prompt:\n\n([\s\S]*?)\n\n")
        user_pattern = re.compile(r"User Prompt:\n\n([\s\S]*?)\n\n")
        model_pattern = re.compile(r"Model Response:\n\n([\s\S]*?)(?=\n\n)")

        # Extract prompts using regex patterns
        system_prompt = system_pattern.search(content).group(1).strip()
        user_prompt = user_pattern.search(content).group(1).strip()
        model_response = model_pattern.search(content).group(1).strip()

        # Prepare messages list
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": model_response},
        ]

        # Add the EMR fields and dictionary to the messages list
        emr_fields_pattern = re.compile(
            r"Data Fields for EMR:(.*?)\n\nAdditional information", re.DOTALL)
        dictionary_pattern = re.compile(
            r"Dictionary:(.*?)\n\nMake sure", re.DOTALL)

        emr_fields_match = emr_fields_pattern.search(content)
        dictionary_match = dictionary_pattern.search(content)

        user_messages = []

        if self.transcription:
            user_messages.append(f"Transcription:\n\n{self.transcription}")

        if emr_fields_match:
            emr_fields = emr_fields_match.group(1).strip()
            user_messages.append(f"Data Fields for EMR:\n\n{emr_fields}")

        if dictionary_match:
            dictionaries = dictionary_match.group(1).strip().split('\n\n')
            combined_dictionary = "\n\n".join(dictionaries[-2:])
            user_messages.append(f"Dictionary:\n\n{combined_dictionary}")

        if user_messages:
            messages.append(
                {"role": "user", "content": "\n\n".join(user_messages)})

        return messages
    
    def store_chat_history(self, messages):
        with open(self.file_path, 'a', encoding='utf-8') as file:
            for message in messages:
                file.write(f"{message['role']}: {message['content']}\n\n")

    def response(self, messages):
        response = CLIENT.chat.completions.create(
            model='gpt-4',
            messages=messages,
        )
        return response

    def generate_responses(self) -> list:
        messages = self.generate_messages()
        final_response = ''
        first_chat = messages[0:3]
        first_chat_response = self.response(first_chat)
        message_from_server = {
            'role': 'assistant',
            'content': first_chat_response.choices[0].message.content,
        }
        first_chat.append(message_from_server)
        messages = first_chat + messages[3:]
        final_response = self.response(messages).choices[0].message.content
        to_add = {
            'role': 'assistant',
            'content': final_response,
        }
        messages.append(to_add)
        self.messages = messages
        self.store_chat_history(messages)
        return final_response
    
    def update_after_clarification_question(self, answer):
        messages = self.messages
        new_message = {
            'role': 'user',
            'content': answer,
        }
        messages.append(new_message)
        response = self.response(messages).choices[0].message.content
        self.messages = messages
        self.store_chat_history(messages)
        return response