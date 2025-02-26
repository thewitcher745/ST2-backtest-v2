import argparse
from dotenv import dotenv_values

# Set up argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=str, help='File name of the output')
parser.add_argument('--pl', type=str, help='File name of the pair list CSV')
parser.add_argument('--position_type', type=str, help='Limit the direction of the positions (short/long)')
parser.add_argument('--timeframe', type=str, help='Override the timeframe set by the params file.')
parser.add_argument('--processes', type=str, help='Maximum number of processes to use while multiprocessing.')

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
pair_list_filename = args.pl if args.pl else None
position_type = args.position_type.lower() if args.position_type else None
timeframe = args.timeframe if args.timeframe else params['timeframe']
max_processes = int(args.processes) if args.processes else 4


