Web scraper to scrape troop information from bannerlord fandom wiki

# How to use
## Setup
### Create python virtual environment and activate

```
python -m venv venv
.\venv\Scripts\activate  // For Windows
```

### Use the requirements.txt file to install the required modules

```
pip install -r requirements.txt
```

## Scripts and their uses

### 1. generate_items_sql.py
Creates the .sql file necessary for generating troop equipment joint table from the items\items.csv file

### 2. create_item_map_enchanced.py
Reads the .csv files in items\ folder and creates normal and reverse maps to be able to identify the items by both their names and their ids

### 3. run_scraper_improved.py
Scrapes the troop information from bannerlord wiki and creates the troop equipment junction table using the previously generated items.sql file and the item maps

Modify this script to add further scraping logic

