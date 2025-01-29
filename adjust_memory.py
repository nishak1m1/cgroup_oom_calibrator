# adjust_memory.py

from logging_config import setup_logging
import logging

setup_logging()

logger = logging.getLogger(__name__)

def allocate_mem_from_selected_cgroups(list_of_cgroups, amount_of_memory):
    """Placeholder for allocating memory from selected cgroups proportionally."""
    logger.info(f"Allocating {amount_of_memory} from selected cgroups: {list_of_cgroups}.")

def adjust_cgroup_limit(cgroup, amount_of_memory):
    """Placeholder for adjusting cgroup limits."""
    logger.info(f"Adjusting limits for cgroup {cgroup} with {amount_of_memory}.")
