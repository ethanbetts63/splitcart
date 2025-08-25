import colorama

colorama.init()

class ScraperOutput:
    def __init__(self, command, company, store_name):
        self.command = command
        self.company = company
        self.store_name = store_name
        self.new_products = 0
        self.duplicate_products = 0
        self.pages_scraped = 0
        self.categories_scraped = 0
        self.total_categories = 0

    def update_progress(self, new_products=0, duplicate_products=0, pages_scraped=0, categories_scraped=0, total_categories=0):
        self.new_products += new_products
        self.duplicate_products += duplicate_products
        self.pages_scraped += pages_scraped
        self.categories_scraped = categories_scraped if categories_scraped > self.categories_scraped else self.categories_scraped
        self.total_categories = total_categories if total_categories > self.total_categories else self.total_categories

        output = (
            f"\r{colorama.Fore.YELLOW}Company:{colorama.Style.RESET_ALL} {self.company} | "
            f"{colorama.Fore.CYAN}Store:{colorama.Style.RESET_ALL} {self.store_name} | "
            f"{colorama.Fore.GREEN}New Products:{colorama.Style.RESET_ALL} {self.new_products} | "
            f"{colorama.Fore.RED}Duplicates:{colorama.Style.RESET_ALL} {self.duplicate_products} | "
            f"{colorama.Fore.BLUE}Pages Scraped:{colorama.Style.RESET_ALL} {self.pages_scraped} | "
            f"{colorama.Fore.MAGENTA}Categories:{colorama.Style.RESET_ALL} {self.categories_scraped}/{self.total_categories}"
        )
        self.command.stdout.write(output)

    def finalize(self):
        self.command.stdout.write("\n")
