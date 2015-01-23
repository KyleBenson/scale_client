<?php
if(!isset($argv[1])) exit();
$lookupName = $argv[1];

require "config.php";

$KEY_VAL = "level";

if(!mysql_connect($MYSQL_HOST, $MYSQL_USER, $MYSQL_PASSWD))
	die("Cannot access database server.");
if(!mysql_select_db($MYSQL_DB))
	die("Cannot select database.");

$res = mysql_query("SELECT * FROM {$DB_TABLE}");
if(!$res)
	die("Cannot access table.");
$count = mysql_num_rows($res);
// print("Fetched {$count} record(s).".PHP_EOL);

$i = 0;
$de_dup = array();
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
	if($ident != $lookupName){ ++$i; continue; }

	$ptime = $decoded_gpstamp["ptime"];
	$lon = $decoded_gpstamp["lon"];
	$lat = $decoded_gpstamp["lat"];
	$alt = $decoded_gpstamp["alt"];
	if(!isset($lon) || !isset($lat)){ ++$i; continue; }
	$level = $value["stats"]["level"];
	$quality = $value["stats"]["quality"];

	$item = array(
		"timestamp" => $timestamp,
		"ptime" => $ptime,
		"lon" => $lon,
		"lat" => $lat,
		"alt" => $alt,
		"quality" => $quality,
		"level" => $level
	);
	if(!isset($de_dup[$ptime]) or $de_dup[$ptime][$KEY_VAL] < $item[$KEY_VAL])
		$de_dup[$ptime] = $item;
	++$i;
endwhile;

$grid = array();
foreach($de_dup as $item):
	$timestamp = $item["timestamp"];
	$ptime = $item["ptime"];
	$lon = $item["lon"];
	$lat = $item["lat"];
	$alt = $item["alt"];
	$quality = $item["quality"];
	$level = $item["level"];
	$round_lon = $lon*$ROUND_MUL;
	$round_lat = $lat*$ROUND_MUL;
	if(!isset($grid[$round_lon])){
		$grid[$round_lon] = array();
	}
	if(!isset($grid[$round_lon][$round_lat])
		|| $timestamp - $grid[$round_lon][$round_lat]["timestamp"] > $REFRESH_P
		|| $item[$KEY_VAL] < $grid[$round_lon][$round_lat][$KEY_VAL]
	)
		$grid[$round_lon][$round_lat] = $item;
endforeach;

print "local,ptime,lon,lat,alt,quality,level,".PHP_EOL;
foreach($grid as $round_lon => $x):
	foreach($x as $round_lat => $item):
		$timestamp = $item["timestamp"];
		$ptime = $item["ptime"];
		$lon = $round_lon/$ROUND_MUL; // $item["lon"];
		$lat = $round_lat/$ROUND_MUL; // $item["lat"];
		$alt = $item["alt"];
		$quality = $item["quality"];
		$level = $item["level"];
		print "{$timestamp},{$ptime},{$lon},{$lat},{$alt},{$quality},{$level},".PHP_EOL;
	endforeach;
endforeach;
?>