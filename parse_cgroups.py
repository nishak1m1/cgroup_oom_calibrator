# parse_cgroups.py

def cgroup_parser(cgroups, sampling_interval, sampling_time):
    """Placeholder for cgroup parsing logic."""
    # This function should create sample file collecting data for sampling_interval, every sampling_time
    # from the list of input cgroups provided.
    # This function will create an intermediate JSON file called cgroup_samples.json
    pass

def create_stats_from_sample():
    """Placeholder for creating stats from the sample."""
    # This function will take input as cgroup_samples.json, parse the data,
    # and create a stats_from_samples.json file with output in following
    # form.
    #
    # input_data = {
    #    "cluster_health": {
    #        "memory.limit_in_bytes": {
    #           "mean": 838860800,
    #           "max": 838860800,
    #           "min": 838860800,
    #           "median": 838860800
    #       }
    #   },
    #   "prism": {
    #       "memory.limit_in_bytes": {
    #           "mean": 1715470336,
    #           "max": 1715470336,
    #           "min": 1715470336,
    #           "median": 1715470336
    #       }
    #   }
    pass
