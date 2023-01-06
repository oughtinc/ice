import os

listOfQuestions = [
"Is a hotdog a taco?",
"Should we legalize all drugs?",
"Is water wet?"
]
# promptIn = "You are trying to win the debate using reason and evidence. No more than 1-2 sentences per turn."

# we need a bash prompt that will
# execute recipe file with the above inputs

for question in listOfQuestions:
    print("question!" + question)
    command = f"python debate/recipe.py --question \"{question}\" "
    os.system(command)
