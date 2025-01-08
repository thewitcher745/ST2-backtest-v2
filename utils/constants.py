from dotenv import dotenv_values

params = dotenv_values('.env.params')

timeframe = params['timeframe']
zigzag_window_size = int(params['zigzag_window_size'])
fib_retracement_coeff = float(params['fib_retracement_coeff'])
stoploss_coeff = float(params['stoploss_coeff'])
target_coeff = float(params['target_coeff'])
max_bounces = int(params['max_bounces'])
max_concurrent = int(params['max_concurrent'])
