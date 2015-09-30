<?php

include "../function.php";

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

/* now grab all the trials in database */
if (isset($_GET['appName'])) {
    $query = "SELECT id,trial.name FROM trial INNER JOIN primary_metadata ON primary_metadata.trial = trial.id WHERE primary_metadata.name = 'Application' AND primary_metadata.value = '{$_GET['appName']}'";
} else {
    $query = 'SELECT id,name FROM trial';
}
$result = pg_query($query) or die('Query failed: '.pg_last_error());

$trials = array();

while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    $trials[$line['id']] = $line['name'];
}

pg_free_result($result);
taudb_close($taudb);

header('Content-Type: application/json');
echo json_encode($trials);

?>