import json
import logging
import os
import sys
import time
from typing import Tuple, List, Optional, Any, Dict
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track
from rich.prompt import Prompt

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

console = Console()

SAVED_SEARCHES_DIR = "saved_searches"


def clear_screen():
    if sys.platform.startswith('win'):
        os.system('cls')  # For Windows
    else:
        os.system('clear')  # For Unix/Linux/macOS


def animate_text(text: str, color: str = 'green', delay: float = 0.05):
    for char in text:
        console.print(char, end='', style=f'bold {color}')
        time.sleep(delay)
    console.print()


class GrantFetcher:
    def __init__(self, api_key: str, delay: float = 60 / 9):
        self.api_key = api_key
        self.delay = delay
        self.base_url = "https://api.candid.org/grants/v1/transactions"

    def get_grants_transactions(self, page_number: int, year_range: Tuple[Optional[int], Optional[int]],
                                dollar_range: Tuple[Optional[int], Optional[int]], subjects: List[str],
                                populations: List[str], locations: List[str], support_strategies: List[str]) -> Dict[
                                str, Any]:
        params = self._build_query_params(page_number, year_range, dollar_range, subjects, populations, locations,
                                          support_strategies)
        url = f"{self.base_url}?{urlencode(params)}"
        headers = {
            "accept": "application/json",
            "Subscription-Key": self.api_key
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting grants transactions: {e}")
            raise

    @staticmethod
    def _build_query_params(page_number: int, year_range: Tuple[Optional[int], Optional[int]],
                            dollar_range: Tuple[Optional[int], Optional[int]], subjects: List[str],
                            populations: List[str], locations: List[str], support_strategies: List[str]) -> Dict[
                            str, str]:
        start_year, end_year = year_range
        min_amt, max_amt = dollar_range

        params = {
            "page": page_number,
            "include_gov": "yes",
            "sort_by": "year_issued",
            "sort_order": "desc",
            "format": "json"
        }

        if locations:
            params["location"] = ",".join(locations)
            params["geo_id_type"] = "geonameid"
            params["location_type"] = "area_served"

        if year_range != (None, None):
            params["year"] = ",".join(map(str, range(start_year, end_year + 1)))

        if subjects:
            params["subject"] = ",".join(subjects)

        if populations:
            params["population"] = ",".join(populations)

        if support_strategies:
            params["support"] = ",".join(support_strategies)

        if min_amt is not None:
            params["min_amt"] = min_amt

        if max_amt is not None:
            params["max_amt"] = max_amt

        return params

    def fetch_grants(self, num_pages: int, year_range: Tuple[Optional[int], Optional[int]],
                     dollar_range: Tuple[Optional[int], Optional[int]], subjects: List[str],
                     populations: List[str], locations: List[str], support_strategies: List[str]) -> List[
                    Dict[str, Any]]:
        all_grants = []

        for page_number in track(range(1, num_pages + 1), description="Fetching grants data"):
            try:
                grants_data = self.get_grants_transactions(page_number, year_range, dollar_range, subjects, populations,
                                                           locations, support_strategies)

                if "rows" in grants_data["data"]:
                    all_grants.extend(grants_data["data"]["rows"])
                else:
                    logging.info(f"No grants data found on page {page_number}.")

                time.sleep(self.delay)  # Pause for required delay time

            except Exception as e:
                logging.error(f"An error occurred while fetching grants data on page {page_number}: {e}")
                break

        return all_grants

    @staticmethod
    def save_grants_to_file(grants: List[Dict[str, Any]], output_prefix: str, page_start: int, page_end: int):
        output_file = f"{output_prefix}_pages_{page_start}-{page_end}.json"
        with open(output_file, "w") as f:
            json.dump({"grants": grants}, f, indent=2)
        console.print(f"[bold green]Grants data saved to {output_file}[/bold green]")


def validate_input(value: str, value_type: type, min_value: Optional[int] = None, max_value: Optional[int] = None) -> \
        Optional[Any]:
    if not value:
        return None

    try:
        parsed_value = value_type(value)
        if min_value is not None and parsed_value < min_value:
            raise ValueError(f"Value should be greater than or equal to {min_value}")
        if max_value is not None and parsed_value > max_value:
            raise ValueError(f"Value should be less than or equal to {max_value}")
        return parsed_value
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")


def get_user_input(prompt: str, default_value: Optional[str] = None) -> str:
    if default_value:
        user_input = Prompt.ask(f"{prompt} (default: {default_value})", default=default_value)
        return user_input.strip()
    else:
        return Prompt.ask(prompt).strip()


def display_menu(options: List[str]) -> int:
    console.print("\n[bold blue]Main Menu[/bold blue]")
    for idx, option in enumerate(options, 1):
        console.print(f"[cyan]{idx}. {option}[/cyan]")
    while True:
        menu_choice = Prompt.ask("Please select an option", choices=[str(i) for i in range(1, len(options) + 1)])
        return int(menu_choice)


def save_search_config(config: Dict[str, Any], search_name: str):
    os.makedirs(SAVED_SEARCHES_DIR, exist_ok=True)
    config_file = os.path.join(SAVED_SEARCHES_DIR, f"{search_name}.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    console.print(f"[bold green]Search configuration saved to {config_file}[/bold green]")


def load_search_config(search_name: str) -> Dict[str, Any]:
    config_file = os.path.join(SAVED_SEARCHES_DIR, f"{search_name}.json")
    with open(config_file, "r") as f:
        config = json.load(f)
    console.print(f"[bold green]Search configuration loaded from {config_file}[/bold green]")
    return config


def display_search_parameters(year_range: Tuple[Optional[int], Optional[int]],
                              dollar_range: Tuple[Optional[int], Optional[int]],
                              subjects: List[str], populations: List[str], locations: List[str],
                              support_strategies: List[str], output_prefix: str):
    console.print("\n[bold blue]Current Search Parameters:[/bold blue]")
    console.print(f"Year Range: {year_range[0]} - {year_range[1]}")
    console.print(f"Dollar Range: {dollar_range[0]} - {dollar_range[1]}")
    console.print(f"Subjects: {', '.join(subjects)}")
    console.print(f"Populations: {', '.join(populations)}")
    console.print(f"Locations: {', '.join(locations)}")
    console.print(f"Support Strategies: {', '.join(support_strategies)}")
    console.print(f"Output Prefix: {output_prefix}")


def get_saved_searches() -> List[str]:
    search_files = [f for f in os.listdir(SAVED_SEARCHES_DIR) if f.endswith(".json")]
    return [os.path.splitext(f)[0] for f in search_files]


def main():
    clear_screen()
    animate_text("Welcome to the Candid API Grants Data Fetcher!", color='green')
    animate_text("This tool will guide you through the process of fetching grants data from the Candid API.", color='green')
    animate_text("Press Enter to skip any field and use the default value (if available) or keep the existing value.", color='green')

    api_key = os.getenv("CANDID_API_KEY")
    if not api_key:
        console.print("Error: CANDID_API_KEY is not set in the environment variables.", style='red')
        return

    grant_fetcher = GrantFetcher(api_key)

    year_range = (None, None)
    dollar_range = (None, None)
    subjects = []
    populations = []
    locations = []
    support_strategies = []
    output_prefix = ""

    while True:
        try:

            menu_options = [
                "Enter Search Parameters",
                "Display Current Search Parameters",
                "Fetch Grants Data",
                "Save Search Configuration",
                "Load Search Configuration",
                "Exit"
            ]
            menu_choice = display_menu(menu_options)

            if menu_choice == 1:
                clear_screen()
                console.print("Enter the start year (e.g., 2022)", style="green")
                start_year = validate_input(Prompt.ask("", default=str(year_range[0]) if year_range[0] else "", show_default=False), int, min_value=1900, max_value=2100)
                console.print("Enter the end year (e.g., 2023)", style="green")
                end_year = validate_input(Prompt.ask("", default=str(year_range[1]) if year_range[1] else "", show_default=False), int, min_value=start_year, max_value=2100) if start_year else None
                year_range = (start_year, end_year)

                console.print("Enter the minimum dollar amount (e.g., 25000)", style="green")
                min_amt = validate_input(Prompt.ask("", default=str(dollar_range[0]) if dollar_range[0] else "", show_default=False), int, min_value=0)
                console.print("Enter the maximum dollar amount (e.g., 10000000)", style="green")
                max_amt = validate_input(Prompt.ask("", default=str(dollar_range[1]) if dollar_range[1] else "", show_default=False), int, min_value=min_amt) if min_amt else None
                dollar_range = (min_amt, max_amt)

                console.print("Enter the subjects (comma-separated, e.g., SJ02,SJ05)", style="green")
                subjects_input = Prompt.ask("", default=",".join(subjects), show_default=False)
                subjects = subjects_input.split(",") if subjects_input else []

                console.print("Enter the populations (comma-separated, e.g., PA010000,PC040000)", style="green")
                populations_input = Prompt.ask("", default=",".join(populations), show_default=False)
                populations = populations_input.split(",") if populations_input else []

                console.print("Enter the locations (comma-separated geonameid, e.g., 4671654,4736286)", style="green")
                locations_input = Prompt.ask("", default=",".join(locations), show_default=False)
                locations = locations_input.split(",") if locations_input else []

                console.print("Enter the support strategies (comma-separated, e.g., UA,UB)", style="green")
                support_strategies_input = Prompt.ask("", default=",".join(support_strategies), show_default=False)
                support_strategies = support_strategies_input.split(",") if support_strategies_input else []

                console.print("Enter a name for your search results file (default: current timestamp)", style="green")
                output_prefix = Prompt.ask("", default=output_prefix if output_prefix else time.strftime("%Y%m%d_%H%M%S"), show_default=False)

            elif menu_choice == 2:
                clear_screen()
                display_search_parameters(year_range, dollar_range, subjects, populations, locations, support_strategies, output_prefix)
                Prompt.ask("Press Enter to continue...")

            elif menu_choice == 3:
                clear_screen()
                animate_text("Contacting the Candid Server...", color='yellow')
                try:
                    grants_data = grant_fetcher.get_grants_transactions(1, year_range, dollar_range, subjects, populations, locations, support_strategies)
                    animate_text("Connection Established! Gathering Results...", color='green')
                    total_hits = grants_data["data"]["total_hits"]
                    total_pages = grants_data["data"]["num_pages"]
                    console.print(f"Total hits: {total_hits}", style='blue')
                    console.print(f"Total pages: {total_pages}", style='blue')

                    console.print("Enter the number of pages to fetch", style="green")
                    num_pages = validate_input(Prompt.ask("", default="10", show_default=False), int, min_value=1, max_value=total_pages)

                    grants = grant_fetcher.fetch_grants(num_pages, year_range, dollar_range, subjects, populations, locations, support_strategies)
                    grant_fetcher.save_grants_to_file(grants, output_prefix, 1, num_pages)
                    console.print(f"Total grants fetched: {len(grants)}", style='green')

                    console.print("Do you want to fetch more pages? (Y/N)", style="green")
                    continue_choice = Prompt.ask("", default="N", show_default=False)
                    if continue_choice.upper() == "Y":
                        remaining_pages = total_pages - num_pages
                        if remaining_pages > 0:
                            console.print(f"Enter the number of additional pages to fetch (max {remaining_pages})", style="green")
                            additional_pages = validate_input(Prompt.ask("", default=str(remaining_pages), show_default=False), int, min_value=1, max_value=remaining_pages)
                            additional_grants = grant_fetcher.fetch_grants(additional_pages, year_range, dollar_range, subjects, populations, locations, support_strategies)
                            grants.extend(additional_grants)
                            grant_fetcher.save_grants_to_file(grants, output_prefix, num_pages + 1, num_pages + additional_pages)
                            console.print(f"Total grants fetched: {len(grants)}", style='green')
                        else:
                            console.print("No more pages available to fetch.", style='yellow')
                except requests.exceptions.RequestException:
                    animate_text("Error connecting to the Candid Server. Please try again later.", color='red')

            elif menu_choice == 4:
                clear_screen()
                console.print("Enter a name for the search configuration", style="green")
                search_name = Prompt.ask("")
                search_config = {
                    "year_range": year_range,
                    "dollar_range": dollar_range,
                    "subjects": subjects,
                    "populations": populations,
                    "locations": locations,
                    "support_strategies": support_strategies,
                    "output_prefix": output_prefix
                }
                save_search_config(search_config, search_name)

            elif menu_choice == 5:
                clear_screen()
                saved_searches = get_saved_searches()
                if saved_searches:
                    console.print("Saved Searches:", style='blue')
                    for idx, search_name in enumerate(saved_searches, 1):
                        console.print(f"{idx}. {search_name}", style='cyan')
                    search_choice = int(Prompt.ask("Please select a search configuration", choices=[str(i) for i in range(1, len(saved_searches) + 1)]))
                    selected_search = saved_searches[search_choice - 1]
                    search_config = load_search_config(selected_search)
                    year_range = search_config["year_range"]
                    dollar_range = search_config["dollar_range"]
                    subjects = search_config["subjects"]
                    populations = search_config["populations"]
                    locations = search_config["locations"]
                    support_strategies = search_config["support_strategies"]
                    output_prefix = search_config["output_prefix"]
                else:
                    console.print("No saved search configurations found.", style='yellow')

            elif menu_choice == 6:
                clear_screen()
                console.print("Thank you for using the Candid API Grants Data Fetcher!", style='green')
                break

        except ValueError as e:
            console.print(f"Error: {e}", style='red')
        except Exception as e:
            console.print(f"An error occurred: {e}", style='red')

if __name__ == "__main__":
    main()