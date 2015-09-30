<?php
include "../function.php";

$trialId  = $_GET['trialId'];

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

$query = "SELECT name,value FROM primary_metadata WHERE trial={$trialId}";
$result = pg_query($query) or die('Query failed: '.pg_last_error());

$metadata = array();
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    $metadata[$line['name']] = $line['value'];
}

pg_free_result($result);
taudb_close($taudb);

header('Content-Type: application/json');
echo json_encode($metadata);

?>