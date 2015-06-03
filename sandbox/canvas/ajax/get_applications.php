<?php

include "../function.php";

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

$query = "SELECT DISTINCT value FROM primary_metadata WHERE name='Application' ORDER BY value";
$result = pg_query($query) or die('Query failed: '.pg_last_error());
$applications = pg_fetch_all_columns($result);
pg_free_result($result);

taudb_close($taudb);

header('Content-Type: application/json');
echo json_encode($applications);

?>