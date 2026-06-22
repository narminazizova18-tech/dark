# Welcome to My Dark Sky
***

## Task
The Problem:
Users often struggle to find a streamlined, ad-free weather dashboard that provides both real-time data and multi-day forecasts in a single view. Accessing this data through various APIs can be slow, and repeated requests for the same location can lead to unnecessary network latency and API rate-limit exhaustion.

The Challenge:
Data Persistence: Building an efficient server-side caching mechanism to store API responses temporarily.
API Management: Handling asynchronous calls to OpenWeatherMap for both current conditions and 5-day forecasts simultaneously.
User Experience: Creating a "Search-as-you-type" city suggestion engine and integrating browser-based geolocation for an "instant-on" experience.

## Description
I developed a full-stack web application using Python (Flask) for the backend and Vanilla JavaScript for the frontend.
Caching Engine: Using SQLAlchemy, I created a database-backed caching layer. When a user requests weather data, the server checks if the data for those coordinates is already in the local weather.db.
If the data is less than 5 minutes old, it is served immediately from the cache, bypassing the external API.
Frontend Architecture: The UI is built with Bootstrap 5 and custom CSS, utilizing a "Glassmorphism" aesthetic. The frontend interacts with the Flask API endpoints via the Fetch API to update the DOM dynamically without page reloads.
Geocoding & Location: The app includes a geocoding search route that suggests cities based on user input and a geolocation module that detects the user's current physical position.

## Installation
To set up the project on your local machine or a Qwasar terminal, follow these steps:

Clone the repository:
Bash
git clone [your-repository-link]
cd [your-project-folder]
Create and activate a virtual environment:

Bash
python3 -m venv venv
source venv/bin/activate
Install dependencies:

Bash
pip install -r requirements.txt

## Usage
To launch the server, run the app.py script:

Bash
python3 app.py
Once the server is active:
Open your browser and navigate to http://127.0.0.1:5000.
Manual Search: Type a city name in the search bar. The system will provide a dropdown of matching locations.
GPS Location: Click the button to allow the browser to detect your current location.
Weather View: View the current temperature, humidity, and wind speed, followed by a 5-day forecast grid below.

### The Core Team
murshudl_m


<span><i>Made at <a href='https://qwasar.io'>Qwasar SV -- Software Engineering School</a></i></span>
<span><img alt='Qwasar SV -- Software Engineering School's Logo' src='https://storage.googleapis.com/qwasar-public/qwasar-logo_50x50.png' width='20px' /></span>
