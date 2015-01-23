<?php
require "config.php";

if(!mysql_connect($MYSQL_HOST, $MYSQL_USER, $MYSQL_PASSWD))
	die("Cannot access database server.");
if(!mysql_select_db($MYSQL_DB))
	die("Cannot select database.");

$res = mysql_query("SELECT * FROM {$DB_TABLE}");
if(!$res)
	die("Cannot access table.");
$count = mysql_num_rows($res);
// print("Fetched {$count} record(s).".PHP_EOL);

print "local,ptime,lon,lat,alt,epx,epy,".PHP_EOL;
$i = 0;
while($i < $count):
	$timestamp = mysql_result($res, $i, "timestamp");
	$msg = mysql_result($res, $i, "msg");
	$decoded_msg = json_decode(str_replace("NaN", "null", $msg), true);
	if(!isset($decoded_msg["event"])
		|| $decoded_msg["event"] != "gps_heartbeat"
	){ ++$i; continue; }
	$gpstamp = mysql_result($res, $i, "gpstamp");
	$decoded_gpstamp = json_decode(str_replace("NaN", "null", $gpstamp), true);
	if($decoded_gpstamp["mode"] < 2){ ++$i; continue; }

	$ptime = $decoded_gpstamp["ptime"];
	$lon = $decoded_gpstamp["lon"];
	$lat = $decoded_gpstamp["lat"];
	$alt = $decoded_gpstamp["alt"];
	$epx = $decoded_gpstamp["epx"];
	$epy = $decoded_gpstamp["epy"];
	if(!isset($lon) || !isset($lat)){ ++$i; continue; }
	print "{$timestamp},{$ptime},{$lon},{$lat},{$alt},{$epx},{$epy},".PHP_EOL;
	++$i;
endwhile;
?>
