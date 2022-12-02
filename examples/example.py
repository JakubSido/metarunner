import torch
#

import argparse

parser = argparse.ArgumentParser(description='add two numbers a+b')
parser.add_argument('-a',type=int)
parser.add_argument('-b',type=int)

config = vars(parser.parse_args())

a = torch.tensor(config["a"])
b = torch.tensor(config["b"])

c = a+b

print(c)