
from scrape import scrape_wikipedia_sites
from curate import Curate
from aggregate import aggregate_and_save

if __name__ == '__main__':
    scrape_wikipedia_sites("test_sites.txt", "test1", highres=False)
    scrape_wikipedia_sites("test_sites.txt", "test2", highres=True)
    # c = Curate()
    # c.process_directories("data")
    # aggregate_and_save("data")
