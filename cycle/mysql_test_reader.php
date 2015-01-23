<?php
$MYSQL_HOST = "localhost";
$MYSQL_DB = "scale_cycle";
$MYSQL_USER = "scale_usr";
$MYSQL_PASSWD = "123456";
$DB_TABLE = "events";

if(!mysql_connect($MYSQL_HOST, $MYSQL_USER, $MYSQL_PASSWD))
	die("Cannot access database server.");
if(!mysql_select_db($MYSQL_DB))
	die("Cannot select database.");

$res = mysql_query("SELECT * FROM {$DB_TABLE}");
if(!$res)
	die("Cannot access table.");
$count = mysql_num_rows($res);
print("Fetched {$count} record(s).".PHP_EOL);
?>