class PromptGenerator:
    def __init__(self):
        self.prompts = {
            'ML': {
                'intro': "Welcome to the ML module! Let's get started on your machine learning journey.",
                'quiz': "Prepare for your ML quiz. Answer the following questions carefully:\n1. ...\n2. ...",
                'project': "Design an ML mo del that classifies images using a convolutional neural network (CNN).",
                'feedback': "Provide your feedback on the ML module experience:",
            },
            'iOS': {
                'intro': "Welcome to the iOS module! Let's dive into iOS development.",
                'quiz': "Here's your iOS quiz. Make sure to review your Swift and UIKit basics:\n1. ...\n2. ...",
                'project': "Create a simple iOS app that displays user data using Swift and UIKit.",
                'feedback': "Provide your feedback on the iOS module experience:",
            }
        }

    def get_prompt(self, module_type, prompt_type):
        """Returns a prompt based on the module type (ML or iOS) and the specific prompt type (e.g., 'quiz', 'project')."""
        module_prompts = self.prompts.get(module_type)
        if module_prompts:
            return module_prompts.get(prompt_type, "Invalid prompt type for this module.")
        else:
            return "Invalid module type. Please choose 'ML' or 'iOS'."

# Usage
prompt_gen = PromptGenerator()

# Example: Get an intro prompt for the ML module
ml_intro_prompt = prompt_gen.get_prompt('ML', 'intro')
print(ml_intro_prompt)

# Example: Get a quiz prompt for the iOS module
ios_quiz_prompt = prompt_gen.get_prompt('iOS', 'quiz')
print(ios_quiz_prompt)

# Example: Get a project prompt for ML
ml_project_prompt = prompt_gen.get_prompt('ML', 'project')
print(ml_project_prompt)