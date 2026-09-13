// Legge i dati JSON inseriti nella pagina da PHP.
const dataElement = document.getElementById('events-data');
const allEvents = JSON.parse(dataElement.textContent);

const periodFilter = document.getElementById('period-filter');
const typeFilter = document.getElementById('type-filter');
const statusFilter = document.getElementById('status-filter');

// Restituisce il nome della prima categoria di un evento.
function getEventType(event) {
    if (event.categories && event.categories.length > 0) {
        return event.categories[0].title;
    }
    return 'Altro';
}

// Formatta una data in italiano.
function formatDate(value) {
    if (!value) {
        return 'Non disponibile';
    }
    return new Date(value).toLocaleDateString('it-IT');
}

// Evita che testi esterni vengano interpretati come codice HTML.
function clean(value) {
    const element = document.createElement('div');
    element.textContent = value || '';
    return element.innerHTML;
}

// Inserisce nel filtro tutti i tipi trovati.
const eventTypes = [];

allEvents.forEach(function (event) {
    const type = getEventType(event);

    if (!eventTypes.includes(type)) {
        eventTypes.push(type);
    }
});

eventTypes.sort().forEach(function (type) {
    const option = document.createElement('option');
    option.value = type;
    option.textContent = type;
    typeFilter.appendChild(option);
});

// Prepara la mappa.
const map = L.map('map').setView([20, 0], 2);
const mapLayers = L.layerGroup().addTo(map);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap'
}).addTo(map);

// Prepara i due grafici vuoti.
const timeChart = new Chart(document.getElementById('time-chart'), {
    type: 'bar',
    data: {
        labels: [],
        datasets: [{
            label: 'Numero di eventi',
            data: [],
            backgroundColor: '#1677b8'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

const typeChart = new Chart(document.getElementById('type-chart'), {
    type: 'doughnut',
    data: {
        labels: [],
        datasets: [{
            data: [],
            backgroundColor: [
                '#1677b8',
                '#e34b5f',
                '#27a474',
                '#f3a13b',
                '#7656a8',
                '#39a7a5'
            ]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false
    }
});

// Applica i tre filtri e restituisce gli eventi da mostrare.
function getFilteredEvents() {
    return allEvents.filter(function (event) {
        const correctType =
            typeFilter.value === 'all' ||
            getEventType(event) === typeFilter.value;

        const correctStatus =
            statusFilter.value === 'all' ||
            event.status === statusFilter.value;

        let correctPeriod = true;

        if (periodFilter.value !== 'all') {
            const eventDate = new Date(event.last_geometry_date);
            const days = Number(periodFilter.value);
            const minimumDate = new Date();
            minimumDate.setDate(minimumDate.getDate() - days);
            correctPeriod = eventDate >= minimumDate;
        }

        return correctType && correctStatus && correctPeriod;
    });
}

function updateStatistics(events) {
    const closed = events.filter(function (event) {
        return event.status === 'closed';
    }).length;

    document.getElementById('total-events').textContent = events.length;
    document.getElementById('closed-events').textContent = closed;
    document.getElementById('open-events').textContent = events.length - closed;
}

function updateCharts(events) {
    const years = {};
    const types = {};

    events.forEach(function (event) {
        const date = event.last_geometry_date
            ? new Date(event.last_geometry_date)
            : null;
        const year = date && !isNaN(date.getTime())
            ? date.getFullYear()
            : 'N/D';
        const type = getEventType(event);

        years[year] = (years[year] || 0) + 1;
        types[type] = (types[type] || 0) + 1;
    });

    const yearLabels = Object.keys(years).sort();
    timeChart.data.labels = yearLabels;
    timeChart.data.datasets[0].data = yearLabels.map(function (year) {
        return years[year];
    });
    timeChart.update();

    const typeLabels = Object.keys(types);
    typeChart.data.labels = typeLabels;
    typeChart.data.datasets[0].data = typeLabels.map(function (type) {
        return types[type];
    });
    typeChart.update();
}

function updateMap(events) {
    mapLayers.clearLayers();
    const finalBounds = L.latLngBounds();

    events.forEach(function (event) {
        (event.geometry || []).forEach(function (geometry) {
            try {
                const layer = L.geoJSON({
                    type: geometry.type,
                    coordinates: geometry.coordinates
                }, {
                    style: {
                        color: '#e34b5f',
                        weight: 2,
                        fillOpacity: 0.2
                    }
                });

                const popup =
                    '<b>' + clean(event.title) + '</b><br>' +
                    'Tipo: ' + clean(getEventType(event)) + '<br>' +
                    'Data: ' + clean(formatDate(geometry.date));

                layer.bindPopup(popup);
                layer.addTo(mapLayers);

                const bounds = layer.getBounds();
                if (bounds.isValid()) {
                    finalBounds.extend(bounds);
                }
            } catch (error) {
                console.log('Geometria non valida:', event.id);
            }
        });
    });

    if (finalBounds.isValid()) {
        map.fitBounds(finalBounds, {maxZoom: 6});
    }
}

function updateTable(events) {
    const table = document.getElementById('event-table');
    table.innerHTML = '';

    if (events.length === 0) {
        table.innerHTML =
            '<tr><td class="empty" colspan="5">Nessun evento trovato</td></tr>';
        return;
    }

    events.forEach(function (event) {
        const row = document.createElement('tr');
        const statusText = event.status === 'open' ? 'In corso' : 'Completato';
        const geometryCount = (event.geometry || []).length;

        row.innerHTML =
            '<td>' + clean(event.title) + '</td>' +
            '<td>' + clean(getEventType(event)) + '</td>' +
            '<td>' + clean(formatDate(event.last_geometry_date)) + '</td>' +
            '<td><span class="status ' + event.status + '">' +
                statusText +
            '</span></td>' +
            '<td>' + geometryCount + '</td>';

        table.appendChild(row);
    });
}

// Aggiorna tutta la dashboard.
function updateDashboard() {
    const filteredEvents = getFilteredEvents();

    updateStatistics(filteredEvents);
    updateCharts(filteredEvents);
    updateMap(filteredEvents);
    updateTable(filteredEvents);
}

// Quando cambia un filtro, aggiorna la dashboard.
periodFilter.addEventListener('change', updateDashboard);
typeFilter.addEventListener('change', updateDashboard);
statusFilter.addEventListener('change', updateDashboard);

updateDashboard();
