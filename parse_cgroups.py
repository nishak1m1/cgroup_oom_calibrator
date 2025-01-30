import os
import json
import time
import statistics
from datetime import datetime
import logging
from logging_config import setup_logging

# Data keys for cgroups
DATA_KEYS = [
    "memory.limit_in_bytes",
    "memory.usage_in_bytes",
    "memory.max_usage_in_bytes"
]

OUTPUT_LOG_FILE = "cgroup_data.json"
OUTPUT_STATS_FILE = "cgroup_stats.json"

# Set up logging. Only single instance of calibration_logger.log for every module
setup_logging()
logging = logging.getLogger(__name__)


def generate_cgroup_directories(cgroups):
    """
    Generate cgroup directory paths based on provided cgroup names.
    """
    base_path = "/sys/fs/cgroup/memory"
    directories = [os.path.join(base_path, cgroup) for cgroup in cgroups]
    return directories


def cgroup_parser(cgroups, sampling_interval, sampling_time):
    """
    Collect memory data from the cgroup directories periodically.
    """
    cgroup_directories = generate_cgroup_directories(cgroups)
    cgroup_directories.append("/sys/fs/cgroup/memory")
    log_data = {}

    # Load existing log data if the file exists and is not empty
    if os.path.exists(OUTPUT_LOG_FILE):
        try:
            with open(OUTPUT_LOG_FILE, 'r') as json_file:
                log_data = json.load(json_file)
        except json.JSONDecodeError:
            logging.warning("Corrupted or empty JSON file, resetting data.")

    start_time = time.time()

    while time.time() - start_time < sampling_time:
        timestamp = datetime.now().isoformat()
        for directory in cgroup_directories:
            # Use 'global_memory' for the main memory cgroup
            cgroup_name = os.path.basename(directory) \
                if directory != "/sys/fs/cgroup/memory" else "global_memory"
            if cgroup_name not in log_data:
                log_data[cgroup_name] = []
            cgroup_entry = {"timestamp": timestamp}
            for key in DATA_KEYS:
                file_path = os.path.join(directory, key)
                try:
                    with open(file_path, 'r') as file:
                        cgroup_entry[key] = int(file.read().strip())
                except (FileNotFoundError, ValueError) as e:
                    logging.error(f"Error reading {file_path}: {e}")
                    cgroup_entry[key] = None
            log_data[cgroup_name].append(cgroup_entry)
        
        # Save log data to a JSON file
        with open(OUTPUT_LOG_FILE, 'w') as json_file:
            json.dump(log_data, json_file, indent=4)
        logging.info(f"Log data collected at {timestamp}")

        # Ensure the correct sampling interval
        elapsed_time = time.time() - start_time
        remaining_time = sampling_interval - (elapsed_time % sampling_interval)
        if remaining_time > 0:
            time.sleep(remaining_time)


def create_stats_from_sample():
    """
    Parse the collected data, compute statistics, and save results to a JSON file.
    """
    try:
        with open(OUTPUT_LOG_FILE, 'r') as json_file:
            log_data = json.load(json_file)
    except FileNotFoundError:
        logging.error("Log data file not found. Run the data collection step first.")
        return

    stats_data = {}

    # Compute statistics for each cgroup
    for cgroup_name, entries in log_data.items():
        stats_data[cgroup_name] = {}
        data_points = {key: [] for key in DATA_KEYS}

        for entry in entries:
            for key in DATA_KEYS:
                if entry.get(key) is not None:
                    data_points[key].append(entry[key])

        for key, values in data_points.items():
            if values:
                stats_data[cgroup_name][key] = {
                    "mean": statistics.mean(values),
                    "max": max(values),
                    "min": min(values),
                    "median": statistics.median(values)
                }
            else:
                stats_data[cgroup_name][key] = "No data available"

    # Save statistics to a JSON file
    with open(OUTPUT_STATS_FILE, 'w') as json_file:
        json.dump(stats_data, json_file, indent=4)

    logging.info("Statistics computed")
