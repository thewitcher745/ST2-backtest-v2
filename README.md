# ST2 Backtest v2

This project is a backtesting framework for financial data, specifically designed to work with cached data in the `.hdf5` format. It includes features
for logging, global configuration settings, and calculating a lag-based zigzag on the data and forming positions using it.

## Features

- **Getting Cached Data**: Retrieve cached data in the `.hdf5` format for different pairs and timeframes.
- **Logging and Global Config Settings**: Manage logging and global configuration settings for the backtesting framework.
- **Lag-Based Zigzag Calculation**: Calculate a lag-based zigzag on the financial data to identify pivot points.
- **Calculation of MSB points on the chart**: Using Fibonacci retracement to identify market structure breaks.
- **Dynamic plotting of candlesticks, zigzags, and boxes**: Dynamically manage drawn data to conserve memory and improve performance

## Usage

1. **Clone the Repository**: Clone the repository to your local machine.
    ```bash
    git clone https://github.com/thewitcher745/ST2-backtest-v2.git
    cd ST2-backtest-v2
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

### ver b0.2

- Implemented more algorith related functionality, but much more optimized than the previous version. Can now calculate MSB points and the boxes that
  form the order blocks.
- Implemented optimized charting using lightweight_charts, with dynamic drawing of chart elements.

### ver b0.3

- Added order block detection
- Added dynamic, interactive order block charting using a customized event handling chart system
- Various fixes and QoL changes to make working with the program smoother.