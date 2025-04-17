import os

def get_int_from_env(var: str):
    x = os.getenv(var)
    if not x:
        raise RuntimeError(f"{var} missing from environment!")
    return int(x)

def get_from_env(var: str):
    x = os.getenv(var)
    if not x:
        raise RuntimeError(f"{var} missing from environment!")
    return x