# main module that integrates all other modules

import time
import logging
from check_load import *
from parse_cgroups import *
from manage_global_cgroup import *
from adjust_memory import *
from logging_config import setup_logging

# Set up logging. Only single instance of calibration_logger.log for every module
setup_logging()
logging = logging.getLogger(__name__)

def from_where_to_pick_memory():
    """Determine where to allocate memory."""
    # Return "global" or a list of cgroups
    # in case of global, find min[(Threshold - current memory.max_usage_in_byte),<last stored value from log file>].
    # And update log file with new info before returning.
    return "global"  # Assuming memory allocation from global cgroup for now

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
        if detect_cgroup_ooms(cgroups):
            oom_detected = True
            logging.info("OOM detected. Initiating calibration process.")
            if load_checker():
                decision = from_where_to_pick_memory()
                amount_of_memory = 1024  # Example amount of memory to allocate
                if decision == "global":
                    allocate_mem_from_global_cgroup(amount_of_memory)
                else:
                    allocate_mem_from_selected_cgroup(decision, amount_of_memory)
                    adjust_cgroup_limit(decision, amount_of_memory)
        else:
            if oom_detected and load_checker():
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
