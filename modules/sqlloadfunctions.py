import logging
import pandas as pd
import re
import numpy as np
import sqlite3
import calendar
from datetime import datetime
import pandas as pd
import numpy as np


logger = logging.getLogger("functions")

def tb_load(fs_file_path, db_dir):
    try:
        logger.info(f"Starting to load TB data from {fs_file_path} into {db_dir}...")
        # Open the text file for reading
        with open(fs_file_path, 'r') as file:
            # Read all lines into a list
            lines = file.readlines()

            # Check if line 3 exists (assuming line numbering starts from 0)
            if len(lines) >= 4:
                # Extract and print line 3 (index 2 in Python)
                line_3 = lines[2]

        # Use regular expression to extract the date part
        date_patterns = r'Reporting Periods \d{2}-(\d{2} \d{4})'
        # Use re.search to find the pattern in the input line
        match = re.search(date_patterns, line_3)

        # Parse the input string to extract month and year
        month, year = map(int, match.group(1).split())

        # Check if month is greater than 12, and set it to 12 if it is
        if int(month) > 12:
            month = 12
            
        def get_last_day_of_month(year, month):
            # Get the last day of the month
            last_day = calendar.monthrange(year, month)[1]
            return datetime(year, month, last_day)

        # Get the last day of the month
        currentPeriod = get_last_day_of_month(year, month)

        # Reading the text file into a DataFrame, assuming it's tab-separated
        df = pd.read_csv(fs_file_path, sep='\t', encoding='ISO-8859-1', skiprows=4)
        df.columns = df.columns.str.strip()
        df.rename(columns={'CoCd': 'CompanyCode', 'G/L acct':'GLAccount', 'Short Text': 'GLAccountName', 'Crcy': 'Currency', 'Accumulated Balance':'LCAmount', 'Debit Blnce of Reportng Period':'DebitLC', 'Credit Balance Reporting Per.':'CreditLC'}, inplace=True)
        
        # Remove rows with NaN
        df = df.dropna(subset=['DebitLC'])
        df = df.dropna(subset=['GLAccount'])

        # Function to strip whitespace from strings
        def strip_whitespace(x):
            if isinstance(x, str):
                return x.strip()
            else:
                return x
                
        # Apply the function to all elements in the DataFrame using applymap
        df = df.apply(lambda col: col.map(strip_whitespace))

        # Remove header rows
        df = df[df['DebitLC'] != 'Debit rept.period']

        # Convert amount columns to float
        df['LCAmount'] = df['LCAmount'].str.replace(',', '')
        df['DebitLC'] = df['DebitLC'].str.replace(',', '')
        df['CreditLC'] = df['CreditLC'].str.replace(',', '')
        df['LCAmount'] = df['LCAmount'].astype(float)
        df['DebitLC'] = df['DebitLC'].astype(float)
        df['CreditLC'] = df['CreditLC'].astype(float)

        # Change GLAccount and CompanyCode to String Type
        df['GLAccount'] = df['GLAccount'].astype(int).astype(str)
        df['CompanyCode'] = df['CompanyCode'].astype(str)

        # Convert Credit side of TB to negative
        df['CreditLC'] = -df['CreditLC']

        # Select only necessary columns
        columns_to_keep = ['CompanyCode', 'GLAccount', 'GLAccountName', 'Currency', 'DebitLC', 'CreditLC', 'LCAmount']
        df = df[columns_to_keep]

        # Add MonthDate, Year, Month, and YearPeriod columns
        df['MonthDate'] = currentPeriod
        df['Year'] = df['MonthDate'].dt.year
        df['Month'] = df['MonthDate'].dt.month
        df['YearPeriod'] = df['Year'].astype(str) + df['Month'].astype(str).str.zfill(2)
        
        # Connect to SQLite database
        db_dir = db_dir.replace("\\", "/")
        conn = sqlite3.connect(db_dir)
        cur = conn.cursor()

        # Get unique YearPeriods
        periodList = df['YearPeriod'].unique()

        # Check if table exists and if it already exist, delete rows with existing YearPeriods
        table_name = "TrialBalance"
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        
        try:
            cur.execute(query)
            conn.commit()
            result = cur.fetchone()

            if result is not None:
                cur.execute("delete from " + table_name + " where \"YearPeriod\" in (%s)" % ','.join(['?'] * len(periodList)), periodList)
                conn.commit()

            # push the dataframe to sql 
            df.to_sql(table_name, conn, if_exists="append", index=False)
            logger.info(f"Trial Balance {fs_file_path} successfully loaded into database.")
            return 
        except Exception as e:
            raise
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error loading {fs_file_path} into database. Error: {e}")
        raise

def loadsalestable(excel_file, db_dir):
    try:    
        logger.info(f"Excel file path: {excel_file}")
        
        # Read the Excel file into a pandas dataframe
        df = pd.read_excel(excel_file, sheet_name="Sheet1")
        logger.info("Excel file read into dataframe")
        
        # Convert the 'Year Period' column to datetime format
        df['MonthDate'] = pd.to_datetime(df['Year Period'].astype(str), format='%Y%m')
        
        # Connect to the SQLite database & create cursor object
        conn = sqlite3.connect(db_dir)
        cur = conn.cursor()
        logger.info("Connected to SQLite database")
        
        # Define the table name
        table_name = "SalesTable"
        logger.info(f"Table name: {table_name}")
        
        # Define conditions to remove rows from DB
        YearPeriod = df['Year Period'].astype(str).unique()
        companyList = df['Company'].astype(str).unique()
        
        # Add all conditions into the parameter list
        params = np.append(YearPeriod, companyList)
        
        # Build placeholders for the IN clause
        placeholder_1 = ', '.join('?' for _ in YearPeriod)
        placeholder_2 = ', '.join('?' for _ in companyList)
        
        # Construct SQL Statement to Delete rows fulfilling the conditions
        delete_query = f"DELETE FROM {table_name} WHERE [Year Period] IN ({placeholder_1}) AND [Company] IN ({placeholder_2})"
        
        # Check if the table exist
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        cur.execute(query)
        conn.commit()
        result = cur.fetchone()
        
        # Execute DELETE statement if exist
        if result is not None:
            cur.execute(delete_query, params)
            conn.commit()
            logger.info("Executed DELETE statement for {placeholder_1} and {placeholder_2}")
        
        # Insert dataframe/table into SQL Database
        df.to_sql(table_name, conn, if_exists='append', index=False)
        logger.info("Inserted dataframe into SQL Database")
        
    except Exception as e:
        logger.error(f"Error loading SAP configuration. Error: {e}")
        return e
    finally:
        cur.close()
        conn.close()
        logger.info("Closed connection")