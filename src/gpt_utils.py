import os
from copy import deepcopy

import openai
import yaml
import tiktoken
from dotenv import load_dotenv

with open('api_settings.yaml', 'r') as f:
    settings = yaml.safe_load(f)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

openai.api_key = os.environ.get('OPENAI_TOKEN')


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(settings['MODEL_NAME'])
    num_tokens = len(encoding.encode(string))
    return num_tokens


system_prompt = open(f"prompts/{settings['SYSTEM_PROMPT']}", "r")
system_prompt = {'role': 'system', 'content': system_prompt.read()}
system_prompt_length = num_tokens_from_string(system_prompt['content'])


def list_availiable_models():
    data = openai.Engine.list()
    for eng in data['data']:
        print(eng['id'])


def get_answer(messages):
    response = openai.ChatCompletion.create(
        model=settings['MODEL_NAME'],
        messages=messages,
        temperature=settings['TEMPERATURE'],
        max_tokens=settings['MAX_TOKENS'],
    )
    return response['choices'][0]['message']['content']


def validate_user_message_lenght(user_message):
    lenght = num_tokens_from_string(user_message) + system_prompt_length
    if lenght > settings['MAX_MESSAGES_LENGHT']:
        return False
    else:
        return True


def cut_messages_by_lenght(messages):
    new_massage_length = 0
    messages_copy = deepcopy(messages)
    filtered_messages = list()

    # удялем системный промпт из списка сообщений
    for index, m in enumerate(messages_copy):
        if m['role'] == 'system':
            messages_copy.pop(index)

    # Проверка на адекватность системного промта
    if settings['MAX_MESSAGES_LENGHT'] <= system_prompt_length:
        raise ValueError('Слишком длинный системный промт!')
    else:
        # все ок, запихиваем в финальный список системный промпт
        filtered_messages.append(system_prompt)

    # забираем последнее сообщение (самое новое)
    new_message = messages_copy[-1]
    new_massage_length += num_tokens_from_string(new_message['content'])
    messages_copy.pop(-1)

    # тут определим какие сообщения из истории влезают и добавляем их в финальный список
    # указываем длину обязательных сообщений
    mandatory_length = new_massage_length + system_prompt_length
    filtered_other_messages = list()

    if len(messages_copy) != 0:
        messages_copy.reverse()
        for index, m in enumerate(messages_copy):
            this_message_length = num_tokens_from_string(m['content'])
            if mandatory_length + this_message_length <= settings['MAX_MESSAGES_LENGHT']:
                filtered_other_messages.append(m)
                mandatory_length += this_message_length

        filtered_other_messages.reverse()
        [filtered_messages.append(m) for m in filtered_other_messages]

    # добавляем самое последнее сообщение
    filtered_messages.append(new_message)

    return filtered_messages


def make_message_list(rows, user_message):

    messages = list()
    [messages.append({'role': list(row)[-2], 'content': list(row)[-1]}) for row in rows]
    messages.append({'role': 'user', 'content': user_message})

    return cut_messages_by_lenght(messages)
