import os

test_debates_instance = None
class TestDebates:

    def __init__(self):

        self.current_prompt = 0
        self.prompts_list = ["You are trying to win the debate using reason and evidence. Don't repeat yourself. No more than 1-2 sentences per turn.",
        "You are trying to win the debate."]
        self.questions_list = ["Is a hotdog a taco?"]

    # getters
    def get_current_prompt(self):
        return self.current_prompt

    def increment_current_prompt(self):
        self.current_prompt = self.current_prompt + 1

    def get_prompts(self):

        return self.prompts_list

    def get_questions(self):

        return self.questions_list
        # "Should we legalize all drugs?",
        # "Is water wet?"


    # @staticmethod
    # def get_instance():
    #     if(TestDebates._instance == None):
    #         TestDebates._instance = TestDebates()
    #         print("new instance of testDebates")
    #     return TestDebates._instance

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

def create_instance():
    global test_debates_instance
    test_debates_instance = TestDebates()
    print(test_debates_instance)

# Initialize our class of prompts/questions
if __name__ == '__main__':
    print(test_debates_instance)

    # initialize instance
    create_instance()

    print(test_debates_instance)
    # immediately start the program based on the prompts/questions
    test_debates_instance.execute_debate()
