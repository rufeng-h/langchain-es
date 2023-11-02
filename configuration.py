import os.path
import torch


class Configuration:
    BASE_DIR = os.path.dirname(__file__)

    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
