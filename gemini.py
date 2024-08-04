
import os

import google.generativeai as genai
import json

genai.configure(api_key=os.getenv('GENAI_API_KEY'))

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json"
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

def invoke(prompt, prev=None):
    base_prompt = (
        "You are a clothing recommender for an e-commerce site where you are given a dictionary of product details. "
        "You have to analyze and answer queries from the user based on the products. If products have to be specified, "
        "then provide its ID like \n{{ \nmessage: <your message as markdown>, \npid: <product id> \n}}\nHere is your \n"
        f"question: {prompt['q']}\nproducts: {prompt['p']}\n"
    )
    
    
    if prev:
        prev_history = "Here is a previous chat history:\n" + str(prev)
    else:
        prev_history = ""

    prompt_text = base_prompt + prev_history + (
        "1.\nNote: 1. Don't return anything other than the specified format.\n"
        "2. Your answer should sound like a human salesperson in a clothing shop and dont use pid in message use the product name instead use pid in respected field only."
        "3.you should return pid in pid field of json as number other wise as 0 but in the case for comparing , you should select one from the given"
    )

    print("prompt text : ",prompt_text)
    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        resp = json.loads(response.text)
        print("response : ",resp)
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        resp = None
    
    return resp

