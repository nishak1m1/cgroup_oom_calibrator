# main module that integrates all other modules

import time
import logging
import json
from check_load import *
from parse_cgroups import *
from manage_global_cgroup import *
from adjust_memory import *
from logging_config import setup_logging

# Set up logging. Only single instance of calibration_logger.log for every module
setup_logging()
logging = logging.getLogger(__name__)
# For current cgroup with oom, what is required amound of memory to be fullfilled
# in current iteration.
requirement = 0

def from_where_to_pick_memory(cgroup_with_oom):
    """Determine where to allocate memory."""
    # Return "global" or a list of cgroups or a null list in case no cgroup have sufficient bw.
    file_path = 'stats_from_samples.json'
    min_usage, max_usage = 0, 0
    try:
        # Open and read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)
        if cgroup_with_oom in data:
            # Extract the "min" value for "memory.usage_in_bytes"
            min_usage = data[cgroup_name].get('memory.usage_in_bytes', {}).get('min')
            max_usage = data[cgroup_name].get('memory.max_usage_in_bytes', {}).get('max')
        else:
            logger.warning(f"The cgroup '{cgroup_with_oom}' is not present in the JSON data.")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error reading JSON file '{file_path}': {str(e)}")
        return []

    requirement = max_usage - min_usage

    if global_cgroup_limit_calculator() >= requirement:
        return "global"
    else:
        cgroups_with_bw = sort_cgroups_with_maximum_memory_bw()
        return cgroups_with_bw

def collect_data(cgroups, sampling_interval, sampling_time):
    """Thread function to collect data when system load is fine."""
    while True:
        if load_checker():
            cgroup_parser(cgroups, sampling_interval, sampling_time)
            create_stats_from_sample()
            global_cgroup_limit_calculator()
        time.sleep(sampling_interval)

def monitor_and_adjust(cgroups, sampling_interval):
    """Thread function to monitor for OOMs and adjust memory limits."""
    previous_limits = {}
    oom_detected = False

    while True:
        cgroup_with_oom = detect_cgroup_ooms(cgroups)
        if cgroup_with_oom:
            logging.info("OOM detected. Initiating calibration process.")
            if load_checker():
                decision = from_where_to_pick_memory(cgroup_with_oom)

                if decision == "global":
                    allocate_mem_from_global_cgroup(requirement, cgroup_with_oom)
                elif decision:
                    allocate_mem_from_selected_cgroup(decision, requirement)
                    adjust_cgroup_limit(decision, requirement)
                else:
                    logging.info("No memory available to allocate.")
        else:
            if cgroup_with_oom and load_checker():
                logging.info("OOM resolved. Reverting limits.")
                revert_limits(cgroups, previous_limits)
                oom_detected = False

        time.sleep(sampling_interval)

def revert_limits(cgroups, previous_limits):
    """Revert cgroups limits to their previous values."""
    for cgroup, limit in previous_limits.items():
        adjust_cgroup_limit(cgroup, limit)
        logging.info(f"Reverted {cgroup} limit to {limit}")

def store_limits(cgroups, previous_limits):
    """Store current limits of cgroups."""
    for cgroup in cgroups:
        # Assuming adjust_cgroup_limit function also retrieves current limits
        current_limit = adjust_cgroup_limit(cgroup, 0)  # Pass 0 to retrieve limit
        previous_limits[cgroup] = current_limit

def from_where_to_pick_memory():
    """Determine where to allocate memory."""
    return "global"  # Assuming memory allocation from global cgroup for now

def main():
    sampling_interval = 300  # 5 minutes
    sampling_time = 60  # 1 minute
    cgroups = ["cluster_health", "prism", "sys_stat_collector"]

    # Store initial limits
    previous_limits = {}
    store_limits(cgroups, previous_limits)

    # Create and start threads
    data_collection_thread = threading.Thread(target=collect_data, args=(cgroups, sampling_interval, sampling_time))
    oom_monitor_thread = threading.Thread(target=monitor_and_adjust, args=(cgroups, sampling_interval))

    data_collection_thread.daemon = True
    oom_monitor_thread.daemon = True

    data_collection_thread.start()
    oom_monitor_thread.start()

    # Main thread will exit, but daemon threads will continue running
    logging.info("Main thread exiting. Daemon threads continue running.")

if __name__ == "__main__":
    main()
