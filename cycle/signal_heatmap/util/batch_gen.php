<?php
if(!isset($argv[1])) exit();
$setName = $argv[1];

require "config.php";
$LIST_AP = true;

$sqlFile = $SQL_FILE_PREFIX.$setName.".sql";
$mysqlCmd = "mysql -u".$MYSQL_USER." -p".$MYSQL_PASSWD." ".$MYSQL_DB;

print "echo \"drop table ".$DB_TABLE.";\" | ".$mysqlCmd.PHP_EOL;
print $mysqlCmd." < ".$sqlFile.PHP_EOL;
print "mkdir ".$setName.PHP_EOL;
print "php mysql_hb_csv.php > ".$setName."/hb.csv".PHP_EOL;
foreach($FIND_AP as $ap):
	print "php mysql_iw_csv.php \"".$ap."\" > \"".$setName."/".$ap.".csv\"".PHP_EOL;
	print "php mysql_iw_csv_level.php \"".$ap."\" > \"".$setName."/".$ap."_level.csv\"".PHP_EOL;
endforeach;
if($LIST_AP)
	print "php mysql_iw_scan.php > ".$setName."/iw.txt".PHP_EOL;
print "echo \"drop table ".$DB_TABLE.";\" | ".$mysqlCmd.PHP_EOL;
?>