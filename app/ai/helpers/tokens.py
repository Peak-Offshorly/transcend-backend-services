import tiktoken

# encoding - cl100k_base for gpt-4, gpt 3
# o200k_base for gpt 4o
def count_tokens(text, encoding_name):
  encoding = tiktoken.get_encoding(encoding_name)
  # encoding = tiktoken.encoding_for_model(encoding_name)
  tokens = len(encoding.encode(text))
  return tokens


#test
# data_to_tokenize = [
  #   trait_type,
#   prompt.template,
#   docs,
#   initial_questions_with_answers,
#   five_traits,
#   chosen_trait,
#   trait_practice,
#   company_size,
#   industry,
#   employee_role,
#   role_description
# ]

# encoding_model = "o200k_base"
# tokens_total = sum(count_tokens(element, encoding_model) for element in data_to_tokenize)
# print(f"Tokens Used: {tokens_total}")
