# Llama2 - Tooly - API - Run Instructions

This document provides step-by-step instructions to set up and run the Llama2 - Tooly - API locally.

## Prerequisites

Before you start, ensure you have the following prerequisites installed on your system:

- [Conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html): for managing the virtual environment.
- [PyTorch](https://pytorch.org/)
- [Uvicorn] (https://www.uvicorn.org/)

## Steps to Run the API

Follow these steps to set up and run the Llama2 - Tooly - API :

### 1. Install dependencies
In the top-level directory run:
pip install -e

### 2. Navigate to the working directory

cd llama/llama

### 3. Activate the Conda Environment

conda activate llama2

### 4. Run the API

torchrun --nproc_per_node 1 apiTooly.py


