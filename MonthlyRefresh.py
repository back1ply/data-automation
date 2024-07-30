import os
import argparse
from pathlib import Path
import modules.mylogger as mylogger
import modules.pbirefresh as pbirefresh
import modules.apirefresh as apirefresh
import modules.aforefresh as afo
import modules.sqlloadfunctions as dataload
import modules.sapguiscripts as sapguiscripts
import modules.systemfx as systemfx

# Declare AFO and SAP related variables
current_dir = Path.cwd()
afotemplate_dir = current_dir / 'templates'
sap_afo_excel_file_sales = afotemplate_dir / "SalesDemo.xlsm"
tb_dir = current_dir / 'sapexport' / 'tb'
keepass_db = Path('./databases/Database.kdbx')
db_dir = Path(r"C:\Users\joel_\joelting\YouTube Demo - General\SQLite Database\FinanceDB.db")

# Declare variables for Power BI Refresh
PowerBIRefreshDirectory = Path(r"C:\Users\joel_\joelting\YouTube Demo - General\Power BI Refresh\Power BI Data Project Refresh")
PowerBIFileTriggerName = "PowerBI Refresh " + systemfx.get_current_time_string() + ".txt"

# Initialize the logger
os.system("")
logger = mylogger.init_logger(current_dir)

# Define command-line arguments
parser = argparse.ArgumentParser(description="Process and load SAP AFO Excel files into the database.")
parser.add_argument('--year', type=int, nargs='+', required=True, help='Specify the input years (e.g., 2024 2025).')
parser.add_argument('--period', type=int, nargs='+', required=True, help='Specify the input periods/months (e.g., 5 6).')
parser.add_argument('--sections', type=str, nargs='+', help='Specify which sections to run (e.g., tb sales exch). If not provided, all sections will be run.')

# Parse the arguments
args = parser.parse_args()
sections = args.sections if args.sections else []
inputYears = args.year if isinstance(args.year, list) else [args.year]
inputPeriods = args.period if isinstance(args.period, list) else [args.period]

def process_and_load_data(year, period, section):
    """
    Process and load data based on the section specified.
    
    Parameters:
    year (int): The year for the data processing.
    period (int): The period (month) for the data processing.
    section (str): The section of data to process ('exch', 'sales', or 'tb').
    """
    
    if section == "tb":
        # Extract trial balance data for the specified year and period
        systemfx.check_and_create_directory(tb_dir)
        new_tbfile = sapguiscripts.f08extract(year, period, keepass_db, str(tb_dir))
        # Load the extracted trial balance data into the database
        dataload.tb_load(new_tbfile, str(db_dir))
    elif section == "sales":
        # Process the SAP Excel file for sales data for the specified year and period
        new_salesfile = afo.process_sap_excel_varyearperiod(sap_afo_excel_file_sales, keepass_db, year, period)
        # Load the processed sales data into the database
        dataload.loadsalestable(new_salesfile, str(db_dir))
    elif section == "exch":
        # Update exchange rates for the specified year and period
        apirefresh.update_exchange_rate(year, period, str(db_dir))


# Iterate over each year in the input years
for year in inputYears:
    # Iterate over each period in the input periods
    for period in inputPeriods:
        if sections:
            # If specific sections are provided, process each section
            for section in sections:
                logger.info(f"Processing section {section} for year {year} and period {period}...")
                process_and_load_data(year, period, section)
                logger.info(f"Section {section} for year {year} and period {period} processed successfully.")
        else:
            # If no specific sections are provided, run all sections
            logger.info(f"Processing all sections for year {year} and period {period}...")
            process_and_load_data(year, period, "exch")
            process_and_load_data(year, period, "sales")
            process_and_load_data(year, period, "tb")
            logger.info(f"All sections for year {year} and period {period} processed successfully.")


# Trigger the Power BI Refresh
pbirefresh.create_blank_text_file(PowerBIRefreshDirectory, PowerBIFileTriggerName)