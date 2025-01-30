from flask import Flask, render_template, request, jsonify
import ollama
import re
import threading
import base64
import io
import time
import random as r
import matplotlib.pyplot as plt
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Enable CORS for the entire app

# Initialize the graph generator and start it
class GraphGenerator:
    def __init__(self):
        self.running = True
        self.encoded_img = None  # Base64 encoded graph image
        self.data = []  # Store CO2 emissions data
        self.thread = threading.Thread(target=self.update_graph, daemon=True)

    def update_graph(self):
        """
        Continuously generate and update a graph in a separate thread.
        """
        while self.running:
            # Generate random data for the graph
            current_time = datetime.now().strftime("%H:%M:%S")
            co2_emission = r.uniform(0.1, 2.0)  # Random CO2 emission value
            self.data.append((current_time, co2_emission))

            # Keep only the last 10 data points
            if len(self.data) > 10:
                self.data.pop(0)

            # Create the graph
            times, emissions = zip(*self.data)
            plt.figure(figsize=(6, 4))
            plt.plot(times, emissions, marker='o')
            plt.title("CO2 Emissions from Electricity Over Time")
            plt.xlabel("Time")
            plt.ylabel("CO2 Emissions (kg)")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save the graph to a BytesIO object
            img_io = io.BytesIO()
            plt.savefig(img_io, format='png')
            plt.close()
            img_io.seek(0)

            # Encode the image to base64
            self.encoded_img = base64.b64encode(img_io.read()).decode('utf-8')

            # Log the update
            time.sleep(1)  # Update graph every 1 second

    def start(self):
        """
        Start the graph generation thread.
        """
        self.thread.start()

    def stop(self):
        """
        Stop the graph generation thread.
        """
        self.running = False
        self.thread.join()

graph_gen = GraphGenerator()
graph_gen.start()

@app.route('/')
def home():
    """
    Serve the HTML template for the client.
    """
    return render_template('index.html')


@socketio.on('request_graph')
def send_graph():
    """
    Send the most recent graph image to the client.
    """
    if graph_gen.encoded_img:
        emit('graph_response', {'image': graph_gen.encoded_img})
    else:
        emit('graph_response', {'image': None, 'error': 'No graph available yet'})

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

    # Get the latest CO2 emissions data
    latest_co2_data = graph_gen.data[-1] if graph_gen.data else ("N/A", 0)
    latest_time, latest_emission = latest_co2_data

    # Create prompt to get advice
    user_message = f"Distance travelled: {distance} km, Mode of transport: {transport}. Carbon footprint: {carbon_footprint} kg CO2."
    co2_message = f"Latest CO2 electricity emission reading at {latest_time}: {latest_emission:.2f} kg."
    intro_message = (
        "You are an expert in environmental sustainability and carbon emissions. "
        "Your task is to provide accurate, data-driven advice on reducing CO₂ emissions. "
        "Use the provided statistics to ensure your advice is practical and relevant. Avoid speculation and assumptions. "
        "Mention the latest electricity CO₂ emissions readings in your advice. "
        "Do not give generic conclusions. "
        "If the CO₂ emissions are already low, acknowledge that and avoid unnecessary suggestions for improvement. "
        "Your response should not exceed 40 words."
    )
    full_prompt = f"{intro_message}\n\nUser stats: {user_message}\n{co2_message}\nDeepSeek:"

    # Generate advice from DeepSeek model
    answer = ollama.generate(model="deepseek-r1:1.5b", prompt=full_prompt)
    response_text = answer.get("response", "")

    # Clean up the response
    cleaned_response = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()

    return jsonify({
        'carbon_footprint': carbon_footprint,
        'advice': cleaned_response
    })

if __name__ == "__main__":
    try:
        # SSL context for secure communication (optional)
        cert_file = 'cert.pem'
        key_file = 'cert.key'

        print("Starting Flask app with SocketIO...")
        socketio.run(app, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("Shutting down the graph generator...")
        graph_gen.stop()
        print("Application stopped.")