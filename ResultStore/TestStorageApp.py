"""Wrapper to run initializers/code in various modules.

Also creates some output folders for CAs and IPMs."""
import api.StorageApi
import services.DatabaseService
import os

os.makedirs("CT", exist_ok=True)
os.makedirs(os.path.join("CT", "CAs"), exist_ok=True)
os.makedirs(os.path.join("CT", "IPMs"), exist_ok=True)
