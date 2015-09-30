<?php
include "../function.php";

function get_thread_name($tid) {
    $tid_map = [
        -1 => "Mean (No Null)",
        -2 => "Total",
        -3 => "Std Dev (No Null)",
        -4 => "Min",
        -5 => "Max",
        -6 => "Mean",
        -7 => "Std Dev",
    ];

    if ($tid >= 0) {
        return $tid;
    } else {
        return $tid_map[$tid];
    }
}

$trialId  = $_GET['trialId'];

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

$query = "SELECT id,thread_index FROM thread WHERE trial={$trialId}";
$result = pg_query($query) or die('Query failed: '.pg_last_error());

$threads = array();
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    $threads[$line['id']] = get_thread_name($line['thread_index']);
}

pg_free_result($result);
taudb_close($taudb);

header('Content-Type: application/json');
echo json_encode($threads);

?>