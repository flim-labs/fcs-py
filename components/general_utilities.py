def calculate_lag_index_length(bin_width=10, tau_high_density=False):
    """
    Calculate the length of lag index based on backend Rust implementation.
    The lag index is generated independently of data_length - no filtering is applied.
    
    Args:
        data_length: The length of the data (not used for filtering, kept for compatibility)
        bin_width: The bin width in microseconds (1, 10, 100, or 1000)
        tau_high_density: True for high density, False for low density
    
    Returns:
        int: The length of the lag index vector
    """
    bin_width_rounded = int(bin_width)
    
    if tau_high_density:
        return _calculate_dense_lag_index_length(bin_width_rounded)
    else:
        return _calculate_standard_lag_index_length(bin_width_rounded)


def _calculate_standard_lag_index_length(bin_width):
    """Calculate length for standard (low density) lag index - matches Rust backend exactly"""
    values = set()  # Use set to automatically handle duplicates
    
    if bin_width == 1:
        # 0..=100
        values.update(range(0, 101))
        # linspace(110, 1000, 49)
        values.update(_linspace(110, 1000, 49))
        # linspace(1100, 10000, 24)
        values.update(_linspace(1100, 10000, 24))
        # linspace(10100, 1_000_000, 24)
        values.update(_linspace(10100, 1_000_000, 24))
        # logspace(1_000_000, 60_000_000, 49)
        values.update(_logspace(1_000_000, 60_000_000, 49))
    elif bin_width == 10:
        # (0..=100).step_by(10)
        values.update(range(0, 101, 10))
        # linspace(110, 1000, 99) mapped to multiples of 10
        lin_values = _linspace(110, 1000, 99)
        values.update((x // 10) * 10 for x in lin_values)
        # linspace(1100, 10000, 49) mapped to multiples of 10
        lin_values = _linspace(1100, 10000, 49)
        values.update((x // 10) * 10 for x in lin_values)
        # linspace(10100, 1_000_000, 49) mapped to multiples of 10
        lin_values = _linspace(10100, 1_000_000, 49)
        values.update((x // 10) * 10 for x in lin_values)
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 10
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 10) * 10 for x in log_values)
    elif bin_width == 100:
        # (0..=100).step_by(100)
        values.update(range(0, 101, 100))
        # linspace(200, 1000, 9)
        values.update(_linspace(200, 1000, 9))
        # linspace(1100, 10000, 49)
        values.update(_linspace(1100, 10000, 49))
        # linspace(10100, 1_000_000, 49)
        values.update(_linspace(10100, 1_000_000, 49))
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 100
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 100) * 100 for x in log_values)
    elif bin_width == 1000:
        # (0..=10_000).step_by(1000)
        values.update(range(0, 10_001, 1000))
        # linspace(11_000, 100_000, 49)
        values.update(_linspace(11_000, 100_000, 49))
        # linspace(100_100, 1_000_000, 49)
        values.update(_linspace(100_100, 1_000_000, 49))
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 1000
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 1000) * 1000 for x in log_values)
    else:
        values.update(range(0, 120))
    
    return len(values)


def _calculate_dense_lag_index_length(bin_width):
    """Calculate length for dense (high density) lag index - matches Rust backend exactly"""
    values = set()  # Use set to automatically handle duplicates
    
    if bin_width == 1:
        # 0..=100
        values.update(range(0, 101))
        # linspace(110, 1000, 99)
        values.update(_linspace(110, 1000, 99))
        # linspace(1100, 10000, 199)
        values.update(_linspace(1100, 10000, 199))
        # linspace(10100, 100000, 199)
        values.update(_linspace(10100, 100000, 199))
        # linspace(100100, 1_000_000, 199)
        values.update(_linspace(100100, 1_000_000, 199))
        # logspace(1_000_000, 60_000_000, 49)
        values.update(_logspace(1_000_000, 60_000_000, 49))
    elif bin_width == 10:
        # (0..=100).step_by(10)
        values.update(range(0, 101, 10))
        # linspace(110, 1000, 99) mapped to multiples of 10
        lin_values = _linspace(110, 1000, 99)
        values.update((x // 10) * 10 for x in lin_values)
        # linspace(1100, 10000, 49) mapped to multiples of 10
        lin_values = _linspace(1100, 10000, 49)
        values.update((x // 10) * 10 for x in lin_values)
        # linspace(10100, 1_000_000, 199) mapped to multiples of 10
        lin_values = _linspace(10100, 1_000_000, 199)
        values.update((x // 10) * 10 for x in lin_values)
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 10
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 10) * 10 for x in log_values)
    elif bin_width == 100:
        # (0..=100).step_by(100)
        values.update(range(0, 101, 100))
        # linspace(200, 1000, 9)
        values.update(_linspace(200, 1000, 9))
        # linspace(1100, 10000, 49)
        values.update(_linspace(1100, 10000, 49))
        # linspace(10100, 1_000_000, 199)
        values.update(_linspace(10100, 1_000_000, 199))
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 100
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 100) * 100 for x in log_values)
    elif bin_width == 1000:
        # (0..=10_000).step_by(1000)
        values.update(range(0, 10_001, 1000))
        # linspace(11_000, 100_000, 99)
        values.update(_linspace(11_000, 100_000, 99))
        # linspace(100_100, 1_000_000, 199)
        values.update(_linspace(100_100, 1_000_000, 199))
        # logspace(1_000_000, 60_000_000, 99) mapped to multiples of 1000
        log_values = _logspace(1_000_000, 60_000_000, 99)
        values.update((x // 1000) * 1000 for x in log_values)
    else:
        values.update(range(0, 120))
    
    return len(values)


def _linspace(start, end, num):
    """Generate linearly spaced values - matches Rust implementation"""
    if num == 0:
        return []
    if num == 1:
        return [end]
    
    result = []
    for i in range(num):
        value = start + round(((end - start) * i) / (num - 1))
        result.append(int(value))
    return result


def _logspace(start, end, num):
    """Generate logarithmically spaced values - matches Rust implementation"""
    import math
    
    if num == 0:
        return []
    if num == 1:
        return [end]
    
    log_start = math.log10(start)
    log_end = math.log10(end)
    
    result = []
    for i in range(num):
        log_value = log_start + ((log_end - log_start) * i) / (num - 1)
        value = round(10 ** log_value)
        result.append(int(value))
    return result



def calculate_expected_intensity_entries(acquisition_time, bin_width):
    return (acquisition_time * 1000) / bin_width