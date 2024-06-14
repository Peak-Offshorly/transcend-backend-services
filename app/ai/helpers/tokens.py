import tiktoken

# encoding - cl100k_base for gpt-4, gpt 3
# o200k_base for gpt 4o
def count_tokens(text, encoding_name):
  encoding = tiktoken.get_encoding(encoding_name)
  # encoding = tiktoken.encoding_for_model(encoding_name)
  tokens = len(encoding.encode(text))
  return tokens
