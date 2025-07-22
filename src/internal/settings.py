# Settings
is_dev = True
is_test = True  # If you don't init, it's True by default


def initialize(dev_mode: bool, is_test: bool = False):
    global is_dev
    is_dev = dev_mode
    is_test = is_test
