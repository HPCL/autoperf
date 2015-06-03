<?php

include "../function.php";

$trialId  = $_GET['trialId'];

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

$query = "SELECT id,name FROM metric WHERE trial={$trialId}";
$result = pg_query($query) or die('Query failed: '.pg_last_error());

$metrics = array();
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    $metrics[$line['id']] = $line['name'];
}

pg_free_result($result);
pg_close($taudb);

header('Content-Type: application/json');
echo json_encode($metrics);

?>