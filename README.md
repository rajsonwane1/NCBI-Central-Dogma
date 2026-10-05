# NCBI Central Dogma

A small bioinformatics web application made with Python, Flask, Biopython and NCBI.

Made by Raj Sonwane and Gaurav Dandire.

## What it does

The application accepts an NCBI accession or a DNA sequence.

For an NCBI accession it retrieves the record, finds the CDS when available, and displays the DNA, RNA and protein sequence along with basic annotation.

For a DNA sequence it cleans the input and translates it in reading frame +1, +2 or +3 using Biopython.

## Running the project

Create a virtual environment.

    python -m venv .venv

Install the required libraries.

    .venv\Scripts\python.exe -m pip install -r requirements.txt

Start the application.

    .venv\Scripts\python.exe app.py

Open this address in a browser.

    http://127.0.0.1:5000

## NCBI

The application uses NCBI E utilities to retrieve nucleotide and protein records. An NCBI email address can be supplied through the NCBI_EML environment variable.

## Files

app.py contains the Flask application and sequence analysis functions.

templates/index.html contains the webpage.

static/style.css contains the styling.

static/app.js handles the interaction between the webpage and the Python backend.

requirements.txt contains the libraries required by the application.
