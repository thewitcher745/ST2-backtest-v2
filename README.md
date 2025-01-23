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

### ver b0.4

- Implemented optimized order block target and stoploss detection: Order blocks have "bounces" (aka multiple chances for entry after getting any exit
  status but stoploss), as well as trailing stoploss configuration. The processing is done by forming "event arrays" which are arrays representing the
  order of events as they happen after the formation of the order block.
- Implemented maximum concurrency of order blocks: Now, the program will keep a set number of order blocks active at all times. Detection of newer
  order blocks will set the end_pdi of the oldest order block in the memory to the formation_pdi of the most recenty found OB.
- Extreme memory and processor efficiency improvement: Rewrote most intensive methods and functions (MSB point detection, order block detection) using
  vectorized Numpy operations and arrays,
  reslting in more than 600% increase in speed and an 80-90% decrease in execution time.
- Added pair-list support: Now fetches the pairs to process from a folder and runs them in succession.
- Updated the charting library with new end_pdi logic for the order blocks.

### ver b0.5

- Implemented custom parameter passing, useful for creating different sets of parameters and using those instead of the ones in `constants.py`.
- Implemented a new launchable main file, `main_param_opt.py`, which will run a number of cases (defined in `/param_opt/param_set_generator.py`), and
  produce a CSV file containing all combinations of those parameters, along with a set of fitness variables defined
  in `/param_opt/fitness_function.py`.
- The output of said code will be in `/reports/param_opt`, and it can be passed into an appropriate program to run more statistical analysis on the
  results.
- Added extra runtime arguments, such as `--output`, which customizes the name of the output file (or directory, in the case of uising the parameter
  optimizer), `--pl` which indicates the pair list to use and `--timeframe` to indicate the timeframe to run the backtest on.
- Added position type and OB box size limiting. The OB box size limiting is done through `constants.py`, while the position type is set through
  the `--position_type` runtime argument. All runtime arguments are applied both to `main.py` and `main_param_opt.py`.
- Number of targets is now set through a `constants.py` parameter as well. This is probably a temporary solution to having dynamic order block
  target_coeff and count.
- Heavily optimized and modularized most of the functions in the backtest which took up the majority of the execution time.