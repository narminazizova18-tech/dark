const cityInput = document.getElementById('citySearch');
const datePicker = document.getElementById('datePicker');
const searchResults = document.getElementById('searchResults');
const weatherDisplay = document.getElementById('weatherDisplay');
const viewWeatherBtn = document.getElementById('viewWeatherBtn');

const state = {
    lat: null,
    lon: null,
    name: '',
};

function formatLabel(dateValue, mode) {
    const date = new Date(`${dateValue}T12:00:00`);
    const prettyDate = date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
    });

    if (mode === 'historical') {
        return `Past weather for ${prettyDate}`;
    }

    if (mode === 'forecast') {
        return `Forecast for ${prettyDate}`;
    }

    return `Today - ${prettyDate}`;
}

function setDefaultDateLimits() {
    const today = new Date();
    const maxDate = new Date();
    maxDate.setDate(today.getDate() + 13);

    datePicker.value = today.toISOString().split('T')[0];
    datePicker.max = maxDate.toISOString().split('T')[0];
}

async function detectLocation() {
    navigator.geolocation.getCurrentPosition((pos) => {
        state.lat = pos.coords.latitude;
        state.lon = pos.coords.longitude;
        state.name = 'Your Location';
        fetchWeather();
    }, () => alert('Location access denied.'));
}

cityInput.addEventListener('input', async (e) => {
    if (e.target.value.length < 3) {
        searchResults.innerHTML = '';
        return;
    }

    const res = await fetch(`/api/search?q=${encodeURIComponent(e.target.value)}`);
    const data = await res.json();

    searchResults.innerHTML = data.map((item) => {
        const label = [item.name, item.admin1, item.country].filter(Boolean).join(', ');
        return `
            <button class="list-group-item list-group-item-action search-result"
                    onclick="selectLocation(${item.lat}, ${item.lon}, '${encodeURIComponent(label)}')">
                ${label}
            </button>
        `;
    }).join('');
});

function selectLocation(lat, lon, name) {
    state.lat = lat;
    state.lon = lon;
    state.name = decodeURIComponent(name);
    cityInput.value = state.name;
    searchResults.innerHTML = '';
    fetchWeather();
}

viewWeatherBtn.addEventListener('click', () => {
    if (state.lat === null || state.lon === null) {
        alert('Choose a location first.');
        return;
    }
    fetchWeather();
});

datePicker.addEventListener('change', () => {
    if (state.lat !== null && state.lon !== null) {
        fetchWeather();
    }
});

async function fetchWeather() {
    searchResults.innerHTML = '';

    const selectedDate = datePicker.value;
    const params = new URLSearchParams({
        lat: state.lat,
        lon: state.lon,
        date: selectedDate,
    });

    const res = await fetch(`/api/weather?${params.toString()}`);
    const data = await res.json();

    if (!res.ok) {
        alert(data.error || 'Unable to load weather data.');
        return;
    }

    renderUI(data);
}

function renderUI(data) {
    weatherDisplay.classList.remove('d-none');

    document.getElementById('locationName').innerText = state.name;
    document.getElementById('selectedDateLabel').innerText = formatLabel(data.selected.date, data.selected.mode);
    document.getElementById('mainTemp').innerText = `${data.selected.temperature}\u00B0`;
    document.getElementById('weatherDesc').innerText = data.selected.description;
    document.getElementById('humidity').innerText = `${data.selected.humidity}%`;
    document.getElementById('wind').innerText = `${data.selected.wind} km/h`;
    document.getElementById('highTemp').innerText = `${data.selected.high}\u00B0`;
    document.getElementById('lowTemp').innerText = `${data.selected.low}\u00B0`;

    document.getElementById('forecastGrid').innerHTML = data.forecast.map((day) => `
        <div class="col">
            <div class="weather-card forecast-card h-100">
                <div class="small text-white-50">${new Date(`${day.date}T12:00:00`).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>
                <div class="forecast-temps">${day.high}\u00B0 / ${day.low}\u00B0</div>
                <div class="small">${day.description}</div>
            </div>
        </div>
    `).join('');
}

setDefaultDateLimits();
