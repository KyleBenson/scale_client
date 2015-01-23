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

$ls = array();
$i = 0;
while($i < $count):
	$timestamp = mysql_result($res, $i, "timestamp");
	$msg = mysql_result($res, $i, "msg");
	$decoded_msg = json_decode(str_replace("NaN", "null", $msg), true);
	if(!isset($decoded_msg["event"])
		|| $decoded_msg["event"] != "gps_iwlist_scan"
	){ ++$i; continue; }
	$gpstamp = mysql_result($res, $i, "gpstamp");
	$decoded_gpstamp = json_decode(str_replace("NaN", "null", $gpstamp), true);
	if($decoded_gpstamp["mode"] < 2){ ++$i; continue; }

	$value = $decoded_msg["value"];
	$ident = $value["ESSID"];
	if($ident == "") $ident = $value["Access Point"];
	if(isset($ls[$ident])){ ++$i; continue; }
	$ls[$ident] = true;
	print $ident.PHP_EOL;
	++$i;
endwhile;
?>