
from scrape import scrape_wikipedia_sites
from curate import Curate
from aggregate import aggregate_and_save

if __name__ == '__main__':
    scrape_wikipedia_sites("sites.txt", "test1", highres=False)
    # c = Curate()
    # c.process_directories("data")
    # aggregate_and_save("data")
