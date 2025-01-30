from flask import Flask, render_template, request, jsonify
import ollama
import re

app = Flask(__name__)

model = "deepseek-r1:1.5b"

intro_message = (
    "You are an expert in environmental sustainability and carbon emissions. "
    "Your task is to provide accurate, data-driven advice on reducing CO₂ emissions, "
    "focusing on travel (flights, cars, public transport), energy consumption, and lifestyle choices. "
    "Use statistics where possible and ensure your advice is practical. Avoid speculation."
    "You shall not ask questions in return but only give advice given a set of data."
    "You will only use normal text as answers without any special formatting, punctuation is allowed."
    "Do not give generic conclusions at the end of your answers."
    "If Co2 emmissions are already good reinforce what they're doing well."
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_advice', methods=['POST'])
def get_advice():
    # Get the user data from the form submission
    distance = request.json.get('distance')
    transport = request.json.get('transport')

    # Determine the carbon footprint
    emission_factors = {
        'car': 0.2,
        'bus': 0.1,
        'bike': 0,
        'train': 0.05,
        'walk': 0,
    }
    emission_factor = emission_factors.get(transport, 0)
    carbon_footprint = distance * emission_factor

    # Create prompt to get advice
    user_message = f"Distance travelled: {distance} km, Mode of transport: {transport}. Carbon footprint: {carbon_footprint} kg CO2."
    full_prompt = f"{intro_message}\n\nUser: {user_message}\nDeepSeek:"

    # Generate advice from DeepSeek model
    answer = ollama.generate(model=model, prompt=full_prompt)
    response_text = answer.get("response", "")

    # Clean up the response
    cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()

    return jsonify({
        'carbon_footprint': carbon_footprint,
        'advice': cleaned_response
    })

if __name__ == '__main__':
    app.run(debug=True)
