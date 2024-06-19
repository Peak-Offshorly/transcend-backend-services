def get_chosen_traits(data):
  chosen_strength = data["chosen_strength"]["name"]
  chosen_weakness = data["chosen_weakness"]["name"]
  return chosen_strength, chosen_weakness

def get_ten_traits(data):
  strengths = [trait["name"] for trait in data["strengths"]]
  weaknesses = [trait["name"] for trait in data["weaknesses"]]
  return strengths, weaknesses

def get_chosen_practices(data):
  strength_practice = None
  weakness_practice = None
  if len(data['chosen_strength_practice']) > 0:
    strength_practice = data['chosen_strength_practice'][0].name
  if len(data['chosen_weakness_practice']) > 0:
    weakness_practice = data['chosen_weakness_practice'][0].name
    
  return strength_practice, weakness_practice