from config import model_slug_to_model_name_map
from datetime import datetime


def date_from_chatgpt_unix_timestamp(ts: str) -> datetime:
    # ts is like 1682000887.0
    # handles 1683712597.463997 too
    return datetime.fromtimestamp(float(ts))


def model_slug_to_model_name(model_slug: str) -> str:
    if model_name := model_slug_to_model_name_map.get(model_slug):
        return model_name
    raise ValueError(f'Unknown model_slug: {model_slug}')

def get_chatgpt_url(id: str) -> str:
    return f'https://chat.openai.com/c/{id}'


def search_and_extract_preview(
    query: str, message: str, return_len: int, case_sensitive: bool = True
) -> str:
    """
    write a python function with args `query, message, return_len: int`, that searches a str `query` inside of a str `message`, if `query in message`, returns a str with len of return_len. the returned str should have `query` in the middle of it.
    add a `case_sensitive` bool arg that controls if the search should be done case-insensitively. note that the returned str should always match the case of that of `message`.
    """
    # query = "world"
    # message = "Hello, World! How are you?"
    # return_len = 15
    # result = search_and_extract_preview(query, message, return_len, case_sensitive=False)
    # print(result)
    if not case_sensitive:
        query = query.lower()
        message_lower = message.lower()
    else:
        message_lower = message

    if query in message_lower:
        if len(query) >= return_len:
            query_start_index = message_lower.index(query)
            return message[query_start_index : query_start_index + return_len]

        query_start_index = message_lower.index(query)
        query_end_index = query_start_index + len(query)

        padding = (return_len - len(query)) // 2
        start_index = max(0, query_start_index - padding)
        end_index = min(len(message), query_end_index + padding)

        while end_index - start_index < return_len:
            if start_index > 0:
                start_index -= 1
            elif end_index < len(message):
                end_index += 1
            else:
                break

        return message[start_index:end_index]
    else:
        return ''
