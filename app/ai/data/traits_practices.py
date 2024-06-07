def get_chosen_traits(data):
  chosen_strength = data["chosen_strength"]["name"]
  chosen_weakness = data["chosen_weakness"]["name"]
  return chosen_strength, chosen_weakness

def get_top_traits(data):
  top_strengths = [trait["name"] for trait in data["strengths"]]
  top_weaknesses = [trait["name"] for trait in data["weaknesses"]]
  return top_strengths, top_weaknesses

def get_chosen_practices(data):
  chosen_strength_practice = data["practices_sprint_1"]["strength_practice"]
  chosen_weakness_practice = data["practices_sprint_1"]["weakness_practice"]
  return chosen_strength_practice, chosen_weakness_practice