import os
import logging
import groq

logger = logging.getLogger(__name__)

class RequirementsAgent:
    """AI agent that transforms a coding prompt into structured requirements using Groq/Qwen3-32b."""
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = groq.Groq(api_key=api_key)
        logger.info("Groq API initialized for RequirementsAgent.")

    def transform_prompt_to_requirements(self, prompt: str) -> dict:
        """
        Transform a freeform coding prompt into a structured requirements dict for a todo item.
        Returns: dict with keys: description, requirements (list), language, context
        """
        system_msg = (
            "You are an expert software project manager. "
            "Given a prompt describing a coding task, extract and structure the following fields for a todo item: "
            "- description: A concise summary of the task. "
            "- requirements: A bullet list of concrete features or requirements. "
            "- language: The main programming language (guess if not specified). "
            "- context: Any additional context or constraints. "
            "Return your answer as a JSON object with these keys."
        )
        user_msg = f"Prompt: {prompt}\n\nReturn a JSON object."
        try:
            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=2048,
                temperature=0.2,
                top_p=0.95
            )
            import json
            content = response.choices[0].message.content.strip()
            # Try to extract JSON from the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                logger.error(f"No JSON found in model response: {content}")
                print("Raw model response:\n", content)
                return {}
        except Exception as e:
            logger.error(f"RequirementsAgent failed: {str(e)}")
            return {}

# Example usage (for testing)
if __name__ == "__main__":
    agent = RequirementsAgent()
    prompt = "Build a web app that lets users upload CSV files and displays summary statistics. Use Python."
    result = agent.transform_prompt_to_requirements(prompt)
    print(result)
    prompt = '''\
{
  "name": "Two-Week China Trip Planning",
  "summary": "A comprehensive, multi-kernel workflow to organize a two-week trip to China covering flights, accommodation, internal transport, activities, and budgeting within a specified budget.",
  "kernels": [
    {
      "name": "Travel Dates Planning",
      "agent_type": "Planner / Travel Consultant",
      "description": "Determine the optimal travel dates considering weather, costs, visa processing, and personal preferences.",
      "inputs": [
        "User preferences",
        "visa requirements",
        "climate info"
      ],
      "outputs": [
        "Finalized travel dates"
      ],
      "dependencies": [],
      "success_criteria": "Selected travel dates are within a suitable window balancing cost, weather, and visa logistics",
      "tools_required": "False",
      "required_tool_types": []
    }
  ]
}
'''
    result = agent.transform_prompt_to_requirements(prompt)
    print(result) 