<?php

function taudb_connect() {
    include "config_local.php";
    return pg_connect("host={$dbhost} dbname={$dbname} user={$dbuser} password='{$dbpass}'");
}

function taudb_close($conn) {
    pg_close($conn);
}

function show_applications() {
    $query = "SELECT DISTINCT value FROM primary_metadata WHERE name='Application' ORDER BY value";
    $result = pg_query($query) or die('Query failed: '.pg_last_error());
    $applications = pg_fetch_all_columns($result);
    pg_free_result($result);

    echo "<div id='application'>\n";
    echo "<ul class='vmenu'>\n";
    echo "\t\t<li class='head'>Application</li>\n";
    $even = false;
    foreach ($applications as $app) {
        $alt = $even ? " class='alt'" : "";

        if (isset($_GET['application']) && ($_GET['application'] == $app)) {
            echo "\t\t<li class='active'><a href='applications.php?application={$app}'>{$app}</a></li>\n";
        } else {
            //echo "\t\t<li{$alt}><a href='applications.php?application={$app}'>{$app}</a></li>\n";
            echo "\t\t<li{$alt}>{$app}</li>\n";
        }

        $even = !$even;
    }
    echo "</ul>\n";
    echo "</div>\n";
}
?>
