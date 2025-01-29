from logging_config import setup_logging
import logging
import queue

setup_logging()

logger = logging.getLogger(__name__)

# Global queue to store memory allocation operations
global_queue = queue.Queue()

# manage_global_cgroup.py
# Most of the global OOM cases are recorded when min watermark is around 15-17% short of free mark.
# So setting the alloc thresholod to 20% of ahead of min mark.
global_oom_thrshld = 20#%
alloc_thrshld_bytes = 0

# Fetches the min and low water mark values.
# Calculate the safer bytes to allocate so that we don't hit global OOM.
# Returns: Safer bytes that can be used for cgroup alloc.
def global_cgroup_limit_calculator():
    try:
        normal_zinfo = "grep -A10 Normal /proc/zoneinfo"
        pattern = "grep -E 'pages free|min'"
        cmd = f"{normal_zinfo} | {pattern}"
        ret = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)

        pages_free = min_mark = None
        for line in ret.stdout.splitlines():
            match = re.search(r'pages free\s+(\d+)', line)
            if match:
                pages_free = int(match.group(1))
            match = re.search(r'min\s+(\d+)', line)
            if match:
                min_mark = int(match.group(1))

        if pages_free is None or min_mark is None:
            raise ValueError("Could not extract values")

        logger.info(f"Pages Free: {pages_free}, Min: {min_mark}")

        if pages_free > min_mark:
            min_percentage = (min_mark / pages_free) * 100
        logger.info(f"% to min_mark: {min_percentage:.2f}")

        alloc_thrshld_prct = min_percentage - global_oom_thrshld
        alloc_thrshld_bytes = int(((alloc_thrshld_prct * pages_free)/100))*4000
        logger.info(f"Safer % short of global OOM: {alloc_thrshld_prct:.2f}")
        logger.info(f"Alloc bytes short of global oom: {alloc_thrshld_bytes}")
        return alloc_thrshld_bytes

    except subprocess.CalledProcessError as e:
        logger.error(f"Command execution failed: {e}")
    except ValueError as e:
        logger.error(f"Parsing error: {e}")

def allocate_mem_from_global_cgroup(amount_of_memory,cgroup_with_oom):
    global_cgroup_path = "/sys/fs/cgroup/memory"
    oom_cgroup_path = os.path.join("/sys/fs/cgroup/memory", cgroup_with_oom)
    try:
        # Decrease memory limit of the global cgroup locally, no in place change required as limit is too high
        with open(os.path.join(global_cgroup_path, 'memory.limit_in_bytes'), 'r+') as global_limit_file:
            current_global_limit = int(global_limit_file.read().strip())
            new_global_limit = current_global_limit - amount_of_memory

        # Log the decrease operation
        logger.info(f"Decreased memory limit of global cgroup by {amount_of_memory} bytes. New limit: {new_global_limit} bytes")

        # Increase memory limit of the cgroup facing OOM
        with open(os.path.join(oom_cgroup_path, 'memory.limit_in_bytes'), 'r+') as oom_limit_file:
            current_oom_limit = int(oom_limit_file.read().strip())
            new_oom_limit = current_oom_limit + amount_of_memory
            oom_limit_file.seek(0)
            oom_limit_file.write(str(new_oom_limit))
            oom_limit_file.truncate()

        # Log the increase operation
        logger.info(f"Increased memory limit of OOM cgroup '{cgroup_with_oom}' by {amount_of_memory} bytes. New limit: {new_oom_limit} bytes")

        # Store the operation in the global queue
        operation_info = {
            "source": global_cgroup_path,
            "amount_taken": amount_of_memory,
            "target": oom_cgroup_path,
            "amount_given": amount_of_memory
        }
        global_queue.put(operation_info)

        # Log the operation stored in the queue
        logger.info(f"Stored operation in global queue: {operation_info}")

    except IOError as e:
        logger.error(f"Failed to allocate memory: {e}")
    except ValueError as e:
        logger.error(f"Invalid memory limit value: {e}")
