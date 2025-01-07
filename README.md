# ST5 Backtest v2

This project is a backtesting framework for financial data, specifically designed to work with cached data in the `.hdf5` format. It includes features
for logging, global configuration settings, and calculating a lag-based zigzag on the data.

## Features

- **Getting Cached Data**: Retrieve cached data in the `.hdf5` format for different pairs and timeframes.
- **Logging and Global Config Settings**: Manage logging and global configuration settings for the backtesting framework.
- **Lag-Based Zigzag Calculation**: Calculate a lag-based zigzag on the financial data to identify pivot points.

## Usage

1. **Clone the Repository**: Clone the repository to your local machine.
    ```bash
    git clone https://github.com/thewitcher745/ST5-backtest-v2.git
    cd ST5-backtest-v2
    ```

2. **Install Requirements**: Install the required dependencies, preferably in a virtualenv.
    ```bash
    pip install -r requirements.txt
    ```

3. **Running**: Load the virtualenv and run `python main.py`

## Changelog

### ver b0.1

- Initial release with the following features:
    - Getting cached data in the `.hdf5` format for different pairs and timeframes.
    - Logging and global config settings.
    - Calculating a lag-based zigzag on the data.

## Repository

For more information, visit the [GitHub repository](https://github.com/thewitcher745/ST5-backtest-v2).