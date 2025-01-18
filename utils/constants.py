import argparse
from dotenv import dotenv_values

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=str, help='File name of the output')
args = parser.parse_args()

params = dotenv_values('.env.params')

timeframe = params['timeframe']
zigzag_window_size = int(params['zigzag_window_size'])
fib_retracement_coeff = float(params['fib_retracement_coeff'])
stoploss_coeff = float(params['stoploss_coeff'])
target_coeff = float(params['target_coeff'])
max_bounces = int(params['max_bounces'])
max_concurrent = int(params['max_concurrent'])
used_capital = float(params['used_capital'])
trailing_sl_target_id = float(params['trailing_sl_target_id'])

ob_size_lower_limit = float(params['ob_size_lower_limit'])    # In percentage of entry price
ob_size_upper_limit = float(params['ob_size_upper_limit'])
n_targets = int(params['n_targets'])

output_filename = args.output if args.output else 'all_positions.xlsx'


