import colorama

colorama.init()

class ScraperOutput:
    def __init__(self, command, company, store_name):
        self.command = command
        self.company = company
        self.store_name = store_name
        self.new_products = 0
        self.duplicate_products = 0
        self.categories_scraped = 0
        self.total_categories = 0

    def update_progress(self, new_products=0, duplicate_products=0, categories_scraped=0, total_categories=0):
        self.new_products += new_products
        self.duplicate_products += duplicate_products
        self.categories_scraped = categories_scraped if categories_scraped > self.categories_scraped else self.categories_scraped
        self.total_categories = total_categories if total_categories > self.total_categories else self.total_categories

        output = (
            f"\r{colorama.Fore.YELLOW}Comp:{colorama.Style.RESET_ALL} {self.company} "
            f"{colorama.Fore.CYAN}Store:{colorama.Style.RESET_ALL} {self.store_name} "
            f"{colorama.Fore.GREEN}New:{colorama.Style.RESET_ALL} {self.new_products} "
            f"{colorama.Fore.RED}Duplicate:{colorama.Style.RESET_ALL} {self.duplicate_products} "
            f"{colorama.Fore.MAGENTA}Cat:{colorama.Style.RESET_ALL} {self.categories_scraped}/{self.total_categories}"
        )
        self.command.stdout.write(output)
        self.command.stdout.flush()

    def finalize(self):
        self.command.stdout.write("\n")
