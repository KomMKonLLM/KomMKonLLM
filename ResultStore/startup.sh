#!/bin/bash

python3 -m jupyter notebook ./Visualisation.ipynb --allow-root --ip 0.0.0.0 &
python3 TestStorageApp.py
