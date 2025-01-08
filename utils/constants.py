from dotenv import dotenv_values

params = dotenv_values('.env.params')

timeframe = params['timeframe']
zigzag_window_size = int(params['zigzag_window_size'])
fib_retracement_coeff = float(params['fib_retracement_coeff'])
