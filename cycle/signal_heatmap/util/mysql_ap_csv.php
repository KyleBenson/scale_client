<?php
if(!isset($argv[2])) exit();
$lookupName = $argv[1];
$keyVal = $argv[2];

if($keyVal != "quality" and $keyVal != "level") exit();

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

$i = 0;
$de_dup = array();
$bssids = array();
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
	$bssid = $value["Access Point"];

	$item = array(
		"timestamp" => $timestamp,
		"ptime" => $ptime,
		"lon" => $lon,
		"lat" => $lat,
		"alt" => $alt,
		"quality" => $quality,
		"level" => $level,
		// "bssid" => $bssid
	);
	if(!isset($de_dup[$ptime]))
		$de_dup[$ptime] = array();
	if(!isset($de_dup[$ptime][$bssid])
		or $de_dup[$ptime][$bssid][$keyVal] < $item[$keyVal]
	)
		$de_dup[$ptime][$bssid] = $item;
	if(!isset($bssids[$bssid]))
		$bssids[$bssid] = null;
	++$i;
endwhile;
// 
// var_dump($bssids);

$grid = array();
foreach($de_dup as $j):
	foreach($j as $bssid => $item):
		$timestamp = $item["timestamp"];
		$ptime = $item["ptime"];
		$lon = $item["lon"];
		$lat = $item["lat"];
		$alt = $item["alt"];
		// $quality = $item["quality"];
		// $level = $item["level"];
		$round_lon = $lon*$ROUND_MUL;
		$round_lat = $lat*$ROUND_MUL;
		if(!isset($grid[$round_lon]))
			$grid[$round_lon] = array();
		if(!isset($grid[$round_lon][$round_lat]))
			$grid[$round_lon][$round_lat] = array();
		if(!isset($grid[$round_lon][$round_lat][$bssid])
			|| $timestamp - $grid[$round_lon][$round_lat][$bssid]["timestamp"] > $REFRESH_P
			|| $item[$keyVal] < $grid[$round_lon][$round_lat][$bssid][$keyVal]
		){
			$grid[$round_lon][$round_lat][$bssid] = $item;
		}
	endforeach;
endforeach;

print "local,ptime,lon,lat,alt,";
$col = 0;
foreach($bssids as $bssid => $whatever):
	$bssids[$bssid] = $col;
	print "$bssid,";
	++$col;
endforeach;
print PHP_EOL;

foreach($grid as $round_lon => $x):
	foreach($x as $round_lat => $y):
		foreach($y as $bssid => $item):
			$timestamp = $item["timestamp"];
			$ptime = $item["ptime"];
			$lon = $round_lon/$ROUND_MUL; // $item["lon"];
			$lat = $round_lat/$ROUND_MUL; // $item["lat"];
			$alt = $item["alt"];
			// $quality = $item["quality"];
			// $level = $item["level"];
			$col = $bssids[$bssid];
			print "{$timestamp},{$ptime},{$lon},{$lat},{$alt},";
			print str_repeat(",", $col);
			print $item[$keyVal];
			print ",".PHP_EOL;
		endforeach;
	endforeach;
endforeach;
?>