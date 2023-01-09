import os

class TestDebates:

    def __init__(self, file_name):
        JSON_loaded = open(file_name)
        self.file_name = file_name
        self.input_data = json.loads(JSON_loaded)

    def reset_prompt_count(self, file_name):

        self.input_data["count"] = 0
        with open(file_name, "w") as outfile:
            json.dump(self.input_data, outfile)
    # getters
    def get_current_prompt(self):
        return self.input_data

    def increment_current_prompt(self):
        self.current_prompt = self.current_prompt + 1

    def get_prompts(self):

        return self.prompts_list

    def get_questions(self):

        return self.questions_list
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
    test_debates_instance = TestDebates()

    # immediately start the program based on the prompts/questions
    test_debates_instance.execute_debate()
