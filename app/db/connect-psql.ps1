$containerName = "nutriscan_postgres"
$databaseName = "nutriscan"
$userName = "nutriscan_user"

docker exec -it $containerName psql -U $userName -d $databaseName
