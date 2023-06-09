import logging


class Logger:
    level_map = {
        "not set": logging.NOTSET,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    def __init__(self, logger_name, filename="ILC_log.log",
                 level="DEBUG", mode="w", tee=False):
        """Initialize ilc_logger class"""

        # Change level to lowercase
        level = level.lower()
        self.level_str = level

        # Set debugging level
        level = self.level_map[level]

        # Set logging parameters
        # Set File Handler
        file_handler = logging.FileHandler(filename, mode.lower())
        
        # Set logging format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname).1s - %(message)s",
            "%M:%S")
        file_handler.setFormatter(formatter)

        # Deactivate logger by default
        file_handler.disabled = True
    
        # Get root logger
        logger = logging.getLogger(str(logger_name))

        # Add new handler
        logger.addHandler(file_handler)
        logger.setLevel(level)

        # Save parameters as class attributes
        self.filename = filename
        self.file_handler = file_handler
        self.tee = tee
        self.level = level
        self.logger = logger
        self.log_funcs = {
            "debug": logger.debug,
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical
        }

    def __del__(self):
        """Called when object is deleted via 'del' or gc"""

        # Run cleanup
        self.cleanup()

    def cleanup(self):
        """Safely destroy class instance"""

        # Deactivate logger file handlers
        self.file_handler.close()
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def __exit__(self):
        """Called when object is quit through with statement"""

        # Run cleanup
        self.cleanup()

    def log(self, *args, **kwargs):
        """Log text to log file"""

        try:
            # Get level from key word arguments
            level = kwargs.pop("level")

        except KeyError:
            
            # Set level to debug as default
            level = self.level_str

        # Set level to lower case level
        level = level.lower()

        # Check if level is not set
        if level != "not set":

            # Make log_text from args
            log_text = " ".join([str(arg) for arg in args])

            # Based on text status call appropriate method
            self.log_funcs[level](log_text, **kwargs)

            # If tee is True, then print log_text to stdout
            if self.tee:
                print(log_text)


