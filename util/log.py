import logging
from colorama import Fore

def setup_logger(name:str, max_level = logging.NOTSET) -> logging.Logger:
    logger = logging.getLogger(name)
    logging.basicConfig(level=logging.INFO)
    # create file handler which logs even debug messages
    #fh = logging.handlers.RotatingFileHandler(f'log/{name}.log', maxBytes=1048576, backupCount=5) # 1MB files
    #fh.setLevel(level)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(max_level) # so we never show DEBUG on stdout
    # create formatter and add it to the handlers
    #file_formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%b %d %Y %H:%M:%S")
    print_formatter = logging.Formatter(Fore.CYAN + "%(asctime)s" + Fore.WHITE + " %(name)s " + Fore.CYAN + "> %(message)s" + Fore.WHITE, "%H:%M:%S")
    #fh.setFormatter(file_formatter)
    ch.setFormatter(print_formatter)
    # add the handlers to the logger
    #logger.addHandler(fh)
    logger.addHandler(ch)

    return logger 

