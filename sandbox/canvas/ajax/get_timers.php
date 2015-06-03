<?php

include "../function.php";

/* mandatory parameters */
$trialId  = $_GET['trialId'];
$threadId = $_GET['threadId'];
$metricId = $_GET['metricId'];

/* optional parameters */
$type     = isset($_GET['type'])   ? $_GET['type']   : "exclusive";
$limit    = isset($_GET['limit'])  ? $_GET['limit']  : 10;
$offset   = isset($_GET['offset']) ? $_GET['offset'] : 0;

$taudb = taudb_connect() or die('Could not connect: ' . pg_last_error());

$query = <<<EOT
SELECT
    timer_call_data.timer_callpath,
    timer.id,
    timer.short_name,
    timer_value.{$type}_value,
    timer_value.{$type}_percent
FROM
    timer_call_data,
    timer_value,
    timer_callpath,
    timer
WHERE
    timer_call_data.id = timer_value.timer_call_data
    AND
    timer_callpath.id = timer_call_data.timer_callpath
    AND
    timer.id = timer_callpath.timer
    AND
    timer_call_data.thread = {$threadId}
    AND
    timer_value.metric = {$metricId}
ORDER BY
    timer_value.{$type}_percent
DESC
LIMIT  {$limit}
OFFSET {$offset}
EOT;

$result = pg_query($query) or die('Query failed: '.pg_last_error());

$timers = pg_fetch_all($result);

pg_free_result($result);
taudb_close($taudb);

header('Content-Type: application/json');
echo json_encode($timers);

?>