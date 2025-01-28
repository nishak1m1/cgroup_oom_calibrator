# Cgroup OOM calibration tool

## Overview
The Cgroup OOM Calibration Tool is designed to monitor and manage memory consumption across cgroups to mitigate Out-Of-Memory (OOM) scenarios. The tool operates in two phases:
Phase 1: Collect and analyze memory consumption data for cgroups over a specified time period.
Phase 2: Dynamically adjust cgroup memory limits in response to OOM events, based on Phase 1 data.
Phase 1: Memory Consumption Analysis

## Goals
Gather memory usage statistics for each cgroup within a specified time period (t1 to t2).
Calculate and store the following for each cgroup:
Minimum memory consumption
Maximum memory consumption
Median memory consumption

## Design
### Input
Time Period: t1 (start time) and t2 (end time).
Cgroups: List of all cgroups to monitor/ all the cgroup 
### Process
Data Collection:
Use memory.stat or similar interfaces to gather memory usage metrics for each cgroup at regular intervals within the specified time period.
Store the collected data in a structured format (e.g., JSON, CSV ????).
### Data Analysis:
Compute the minimum, maximum, and median memory consumption for each cgroup from the collected data.
Save these statistics for use in Phase 2.
### Output
A structured list of cgroups with their memory consumption ranges:
{
  "cgroup_name": {
    "min_consumption": <value>,
    "max_consumption": <value>,
    "median_consumption": <value>
  },
  ...
}

## Phase 2: Dynamic Memory Adjustment
### Goals
Respond to OOM events by dynamically reallocating memory from either of two: Global cgroup limit OR underutilized cgroups to the affected cgroup.
### Design
#### Input
Cgroup OOM Event: Triggered by the system when a cgroup faces an OOM scenario.
Phase 1 Data: Memory consumption ranges for all cgroups.
#### Process
Detect OOM Event:
Monitor system logs or use inotify mechanisms to detect OOM events in cgroups.
Identify from Where to Allocate Memory:
Step 1: Compare the global cgroup limit and its current maximum usage. Determine if memory can be allocated from the global limit (if it is below a certain threshold).
Step 2: If the global limit cannot provide sufficient memory, compare the current memory usage of all cgroups against their median memory consumption (from Phase 1 data).
Step 3: Identify cgroups consuming less memory than expected and evaluate their potential to contribute unused memory.
#### Reallocate Memory:
Calculate the required memory to resolve the OOM.
If allocating memory from the global cgroup, adjust the affected cgroup's memory limit directly without reducing the global memory limit.
If reallocating from underutilized cgroups:
Reduce the memory limits of identified underutilized cgroups proportionally.
Increase the memory limit of the affected cgroup by the calculated amount in its memory.limit_in_bytes.
#### Output Log:
Record memory adjustments for auditing and debugging purposes:
{
  "oom_cgroup": "<name>",
  "added_memory": <value>,
  "adjusted_cgroups": [
    {
      "name": "<name>",
      "reduced_memory": <value>
    },
    ...
  ]
}

## Implementation
Trigger Mechanism:
Use a daemon process or systemd service to monitor and respond to OOM events.
Adjustment Mechanism:
Directly adjust memory.limit_in_bytes of cgroups.
Safety Checks:
Ensure no cgroup is reduced below its minimum memory requirement.
Validate the feasibility of reallocations against system constraints.





