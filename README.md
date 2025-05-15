# Data Axle API Tool

A Flask-based web application for analyzing geographic areas using the Data Axle API.

## Features

- Upload KMZ/KML files to define geographic areas
- Pull business or consumer records for selected areas
- Generate demographic insights reports
- Export results as CSV or KML files

## Setup

### Prerequisites

- Python 3.12 or higher
- Poetry for dependency management
- Data Axle API token

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your Data Axle API token
3. Install dependencies with Poetry:

```bash
poetry install