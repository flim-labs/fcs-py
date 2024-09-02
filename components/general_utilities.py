def calculate_lag_index_length(data_length):
    max_tau = data_length - 1
    scale_factor = max_tau / (3.0 ** (8.0 - 2.0))
    lag_index = []
    exponent = 2.0
    while exponent < 8.0:
        result = round(scale_factor * (3.0 ** exponent))
        lag_index.append(result)
        exponent += 0.05
    lag_index = sorted(set(lag_index))  
    lag_index = [x for x in lag_index if x <= max_tau]
    if len(lag_index) == 0 or lag_index[0] != 0:
        lag_index.insert(0, 0)
    return len(lag_index)


def calculate_expected_intensity_entries(acquisition_time, bin_width):
    return (acquisition_time * 1000) / bin_width