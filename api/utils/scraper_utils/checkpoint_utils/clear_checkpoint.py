from api.utils.scraper_utils.checkpoint_utils.read_checkpoints import read_checkpoints
from api.utils.scraper_utils.checkpoint_utils.write_checkpoints import write_checkpoints

def clear_checkpoint(company_name: str) -> None:
    """
    Clears the checkpoint for a company once scraping is fully complete.

    Args:
        company_name: The name of the company.
    """
    checkpoints = read_checkpoints()
    if company_name in checkpoints:
        del checkpoints[company_name]
        write_checkpoints(checkpoints)