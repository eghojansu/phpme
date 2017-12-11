<?php

include __DIR__.'/Command.php';

$argv = $_SERVER['argv'];
if ($argv && basename($argv[0]) === basename(__FILE__)) {
    array_shift($argv);
}
if ($argv) {
    echo (new Command())->run(array_shift($argv), $argv);
} else {
    echo 'error: No command given';
}
echo PHP_EOL;
