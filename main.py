
from scrape import scrape_wikipedia_sites
from curate import Curate
from aggregate import aggregate_and_save


# FOR THIS TO RUN YOU NEED TWO ADDITIONAL ITEMS:
# 1. YOU NEED A DIRECTORY CALLED "data" at least one subdirectory of images
# 2. YOU NEED A FILE CALLED API_KEY (with your openai API key)

if __name__ == '__main__':
    # scrape_wikipedia_sites("sites.txt")
    c = Curate()
    c.process_directories("data")
    aggregate_and_save("data")
