<?php
// L'indirizzo dell'API viene passato da compose.yaml.
$apiUrl = getenv('NASA_API_URL') ?: 'http://localhost:8000';
$events = [];
$error = '';
$offset = 0;

// L'API permette di leggere 500 eventi alla volta.
// Ripetiamo la richiesta finché abbiamo scaricato tutti gli eventi.
do {
    $url = $apiUrl . '/api/events?status=all&limit=500&offset=' . $offset;
    $json = @file_get_contents($url);

    if ($json === false) {
        $error = 'Impossibile collegarsi all API.';
        break;
    }

    $page = json_decode($json, true);

    if (!is_array($page)) {
        $error = 'I dati ricevuti non sono validi.';
        break;
    }

    $events = array_merge($events, $page);
    $offset += 500;
} while (count($page) === 500);
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>test</title>

    <!-- Fogli di stile della mappa e della dashboard. -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="dashboard">

    <header>
        <h1>prova tecnica</h1>
    </header>

    <?php if ($error !== ''): ?>
        <div class="error"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <section class="section statistics">
        <div class="stat">
            <span>Eventi</span>
            <strong id="total-events">0</strong>
        </div>
        <div class="stat closed">
            <span>Completati</span>
            <strong id="closed-events">0</strong>
        </div>
        <div class="stat open">
            <span>In corso</span>
            <strong id="open-events">0</strong>
        </div>
    </section>

    <section class="section">
        <h2>Filtri</h2>
        <div class="filters">
            <div>
                <label for="period-filter">Periodo</label>
                <select id="period-filter">
                    <option value="all">Tutto il periodo</option>
                    <option value="30">Ultimi 30 giorni</option>
                    <option value="365">Ultimo anno</option>
                </select>
            </div>

            <div>
                <label for="type-filter">Tipo</label>
                <select id="type-filter">
                    <option value="all">Tutti i tipi</option>
                </select>
            </div>

            <div>
                <label for="status-filter">Stato</label>
                <select id="status-filter">
                    <option value="all">Tutti gli stati</option>
                    <option value="open">In corso</option>
                    <option value="closed">Completati</option>
                </select>
            </div>
        </div>
    </section>

    <section class="charts">
        <div class="chart-box">
            <h2>Eventi nel tempo</h2>
            <div class="chart-area">
                <canvas id="time-chart"></canvas>
            </div>
        </div>

        <div class="chart-box">
            <h2>Eventi per tipo</h2>
            <div class="chart-area">
                <canvas id="type-chart"></canvas>
            </div>
        </div>
    </section>

    <section class="section">
        <h2>Mappa eventi</h2>
        <div id="map"></div>
    </section>

    <section class="section">
        <h2>Tabella eventi</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Evento</th>
                        <th>Tipo</th>
                        <th>Data</th>
                        <th>Stato</th>
                        <th>Rilevazioni</th>
                    </tr>
                </thead>
                <tbody id="event-table"></tbody>
            </table>
        </div>
    </section>

</div>

<!-- PHP inserisce i dati nella pagina senza contenere codice JavaScript. -->
<script id="events-data" type="application/json">
    <?= json_encode($events, JSON_HEX_TAG | JSON_HEX_AMP) ?>
</script>

<!-- Librerie esterne e file JavaScript della dashboard. -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="app.js"></script>
</body>
</html>
