<?php
if(!isset($argv[2])) exit();
$ap = $argv[1];
$setNames = array();
$argc = sizeof($argv);
for($j = 2; $j < $argc; ++$j)
	$setNames[] = $argv[$j];
$mergeName = "merge/".$ap."_level.csv";

require "config.php";

$KEY_VAL = "level";

$de_dup = array();
foreach($setNames as $setName):
	$fileName = $setName."/".$ap.".csv";
	$handle = fopen($fileName, "r");
	if(!$handle) exit(-1);
	while(($line = fgets($handle)) != false):
		$arr_line = explode(",", $line);
		// var_dump($arr_line);
		if(!is_numeric($arr_line[0]) or !is_numeric($arr_line[1])) continue;
		if($arr_line[4] != "")
			$alt = floatval($arr_line[4]);
		else $alt = "";
		$item = array(
			"timestamp" => floatval($arr_line[0]),
			"ptime" => floatval($arr_line[1]),
			"lon" => floatval($arr_line[2]),
			"lat" => floatval($arr_line[3]),
			"alt" => $alt,
			"quality" => intval($arr_line[5]),
			"level" => intval($arr_line[6])
		);
		$de_dup[] = $item;
	endwhile;
	// print sizeof($de_dup); print PHP_EOL;
	// var_dump($de_dup);
	fclose($handle);
endforeach;

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

$handle = fopen($mergeName, "w");
fprintf($handle, "local,ptime,lon,lat,alt,quality,level,".PHP_EOL);
foreach($grid as $round_lon => $x):
	foreach($x as $round_lat => $item):
		$timestamp = $item["timestamp"];
		$ptime = $item["ptime"];
		$lon = $round_lon/$ROUND_MUL; // $item["lon"];
		$lat = $round_lat/$ROUND_MUL; // $item["lat"];
		$alt = $item["alt"];
		$quality = $item["quality"];
		$level = $item["level"];
		fprintf($handle,
			"{$timestamp},{$ptime},{$lon},{$lat},{$alt},{$quality},{$level},"
				.PHP_EOL
		);
	endforeach;
endforeach;
fclose($handle);
?>