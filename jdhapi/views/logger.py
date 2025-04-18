import logging

def logger():
    """
    Logger for the application.
    """
    # Set up logging configuration
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(filename)s - L%(lineno)d - %(levelname)s - %(message)s')
    
    return logging