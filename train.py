#!/usr/bin/env python3

import torch

def main() -> None:

    model = torch.nn.Sequential(
            torch.nn.Linear(D_in, H),
            torch.nn.ReLU(),
            torch.nn.Linear(H, D_out),
            )

if __name__ == "__main__":
    main()
