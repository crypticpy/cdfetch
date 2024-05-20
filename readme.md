# Candid API Grants Data Fetcher

Welcome to the Candid API Grants Data Fetcher! This application helps users fetch data from the Candid API - Transactions database and prepares the data for loading into the GrantScope application.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [License](#license)

## Features
- Fetches grant transaction data from the Candid API.
- Allows users to specify search parameters such as year range, dollar amount range, subjects, populations, locations, and support strategies.
- Saves fetched grant data to JSON files.
- Saves and loads search configurations for easy reuse.

## Prerequisites
- Python 3.8 or higher
- [Candid API key](https://candid.org/) (sign up to get an API key)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/candid-api-grants-fetcher.git
   cd candid-api-grants-fetcher
    ```
2. Create virtual environment:
   ```bash
   python -m venv venv
   ```
3. Install the required packages:
   ```bash
      pip install -r requirements.txt
      ```

## Configuration
1. Create a `.env` file in the root directory of the project.
   ```bash
   touch .env
   ```
2. Add the following environment variables to the `.env` file:
   ```bash
   CANDID_API_KEY=your_api_key_here
   ```
   
## Usage
1. Run the application:
   ```bash
   python app.py
   ```
2. Follow the prompts to fetch grant data from the Candid API.
3. Use the saved JSON data into the GrantScope application https://grantscope.streamlit.app/.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
