import os
import json

class TestDebates:

    def __init__(self, file_name):
        JSON_loaded = open(file_name)
        self.file_name = file_name
        self.input_data = json.load(JSON_loaded)

    def reset_prompt_count(self):

        self.input_data["prompt_count"] = 0
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def get_prompts(self):
        return self.input_data["input_prompts"]

    # getters
    def get_current_prompt(self):
        prompts_list = self.get_prompts()
        prompt_count = self.input_data["prompt_count"]
        return prompts_list[prompt_count]

    def increment_current_prompt(self):
        prompt_count = self.input_data["prompt_count"]
        self.input_data["prompt_count"] = prompt_count + 1
        with open(self.file_name, "w") as outfile:
            json.dump(self.input_data, outfile)

    def get_questions(self):

        return self.input_data["input_questions"]
        # "Should we legalize all drugs?",
        # "Is water wet?"

    # we need a bash prompt that will
    # execute recipe file with the above inputs
    def execute_debate(self):

        print(test_debates_instance)

        questions_list = test_debates_instance.get_questions()
        prompts_list = test_debates_instance.get_prompts()

        for prompt in prompts_list:

            for question in questions_list:
                command = f"python debate/recipe.py --question \"{question}\" "
                os.system(command)

            # increment our current prompt
            test_debates_instance.increment_current_prompt()

# Initialize our class of prompts/questions
if __name__ == '__main__':

    # initialize instance
    test_debates_instance = TestDebates("debate/inputs.json")

    # immediately start the program based on the prompts/questions
    test_debates_instance.execute_debate()
