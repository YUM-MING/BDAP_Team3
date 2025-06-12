from .analysis import load_event_data, calculate_time_delays

def prepare_dataset():
    raw_data = load_event_data()
    processed_data = calculate_time_delays(raw_data)
    return processed_data
