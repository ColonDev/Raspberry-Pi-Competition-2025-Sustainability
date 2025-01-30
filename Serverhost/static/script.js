const cards = document.querySelectorAll('.card');
let currentIndex = 0;

function updateCarousel() {
    cards.forEach((card, index) => {
        card.classList.remove('active', 'previous', 'next');
        if (index === currentIndex) {
            card.classList.add('active');
        } else if (index === (currentIndex - 1 + cards.length) % cards.length) {
            card.classList.add('previous');
        } else if (index === (currentIndex + 1) % cards.length) {
            card.classList.add('next');
        }
    });
}

// Initialize the carousel on load
document.addEventListener('DOMContentLoaded', () => {
    updateCarousel();
});

// Navigate to the previous card (with looping)
function prevCard() {
    currentIndex = (currentIndex - 1 + cards.length) % cards.length; // Wrap to the last card
    updateCarousel();
}

// Navigate to the next card (with looping)
function nextCard() {
    currentIndex = (currentIndex + 1) % cards.length; // Wrap to the first card
    updateCarousel();
}

// Graph generation via Socket.IO
const socket = io.connect();

function requestGraph() {
    socket.emit('request_graph'); // Emit request to the server
}

socket.on('graph_response', function (data) {
    const imgElement = document.getElementById('graphImage');
    imgElement.src = "data:image/png;base64," + data.image; // Update the image source
});

// Function to handle the submission of carbon footprint data
function submitCarbonFootprint() {
    // Get user input
    const distance = parseFloat(document.getElementById('distance').value);
    const transport = document.getElementById('transport').value;

    // Validate input
    if (isNaN(distance) || distance <= 0) {
        alert("Please enter a valid distance.");
        return;
    }

    // Send the input to the Flask backend for advice
    fetch('/get_advice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            distance: distance,
            transport: transport
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update the carbon footprint
        document.getElementById('carbon-total').textContent = data.carbon_footprint.toFixed(2);

        // Update the personalised advice
        const adviceElement = document.getElementById('personalised-advice');
        adviceElement.textContent = data.advice;

        // Navigate to the Carbon Footprint Overview card
        currentIndex = 2; // Index of the Carbon Footprint Overview card
        updateCarousel();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}