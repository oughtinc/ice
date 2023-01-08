import os

class TestDebates:

    _instance= None

    def __init__(self):

        self.current_prompt = 0

        self.prompts_list = ["You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.",
        "You are trying to win the debate using reason and evidence. No more than 1-2 sentences per turn."]

        self.questions_list = ["Is a hotdog a taco?"]

    def get_current_prompt(self):
        return self.current_prompt
    def get_prompts(self):

        return self.prompts_list

    def get_questions(self):

        return self.questions_list
        # "Should we legalize all drugs?",
        # "Is water wet?"

    # promptIn = "You are trying to win the debate using reason and evidence. No more than 1-2 sentences per turn."

    # we need a bash prompt that will
    # execute recipe file with the above inputs

    def execute_debate(self):

        questions_list = self.get_questions()

        prompts_list = self.get_prompts()

        for prompt in prompts_list:

            # increment our current prompt
            self.current_prompt = self.current_prompt + 1

            for question in questions_list:
                command = f"python debate/recipe.py --question \"{question}\" "
                os.system(command)
    @staticmethod
    def get_instance():
        if(TestDebates._instance == None):
            TestDebates._instance = TestDebates()
            print("new instance of testDebates")
        return TestDebates._instance
# Initialize our class of prompts/questions
if __name__ == '__main__':

    testDebates = TestDebates.get_instance()

    # immediately start the program based on the prompts/questions
    testDebates.execute_debate()
