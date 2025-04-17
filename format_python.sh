python -m black src  # Command to be executed
python -m isort src
python -m flake8 src --config=setup.cfg # Command to be executed
python -m pyright src # Command to be executed