<?php
//$means variable
$db_server = "localhost";
$db_user = "root";
$db_pass = "";
$db_name = "brocodedb";
//connection variable
$conn = "";
try {
    $conn = mysqli_connect(
        $db_server,
        $db_user,
        $db_pass,
        $db_name
    );
} catch (mysqli_sql_exception) {
    echo "Could not connect <br>";
}
if ($conn) {
    echo "You are connected";
}
// else{
//     echo "Could not connect";
// }

?>