import yfinance as yf
import pandas as pd
import sqlite3
import logging

# Get the logger
logger = logging.getLogger("functions")

def update_exchange_rate(year, month, db_dir):
    try:
        logger.info(f"Starting to get {year}{month:02d} exchange rate data from Yahoo Finance...")

        # List of currencies and their respective Yahoo Finance ticker symbols
        currencies = {
            'AUD': 'AUDUSD=X',
            'BRL': 'BRLUSD=X',
            'EUR': 'EURUSD=X',
            'JPY': 'JPYUSD=X'
        }

        # Date range for the specified month
        start_date = f'{year}-{month:02d}-01'
        end_date = f'{year}-{month:02d}-{pd.Period(start_date).days_in_month}'

        # Create an empty list to store the data
        data = []

        # Loop through each currency and fetch the historical exchange rates
        for currency, ticker in currencies.items():
            # Fetch the historical data from Yahoo Finance
            df = yf.download(ticker, start=start_date, end=end_date, interval='1mo')
            
            # Ensure the index is datetime
            df.index = pd.to_datetime(df.index)
            
            # Add the currency, CalendarYear/Month, and RateType to the DataFrame
            df['Currency'] = currency
            df['CalendarYear/Month'] = df.index.strftime('%m/%Y')
            df['RateType'] = 'IAS Rate'
            df['Exchange Rate'] = df['Close']
            
            # Append the data to the list
            data.append(df[['Currency', 'CalendarYear/Month', 'RateType', 'Exchange Rate']])

        # Create a DataFrame for USD with a constant exchange rate of 1
        usd_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
        usd_data = {
            'Currency': 'USD',
            'CalendarYear/Month': usd_dates.strftime('%m/%Y'),
            'RateType': 'IAS Rate',
            'Exchange Rate': 1.0
        }
        usd_df = pd.DataFrame(usd_data)

        # Append the USD data to the list
        data.append(usd_df)

        logger.info(f"Data extracted from Yahoo Finance. Loading data into database {db_dir}")
        
        # Concatenate all data into a single DataFrame
        result_df = pd.concat(data).reset_index(drop=True)
        result_df['Year'] = result_df['CalendarYear/Month'].str[-4:].astype(int)
        result_df['Period'] = result_df['CalendarYear/Month'].str[:2].astype(int)
        result_df['StartDate'] = pd.to_datetime(result_df['Year'].astype(str) + result_df['Period'].astype(str), format='%Y%m')
        result_df['EndDate'] = result_df['StartDate'] + pd.offsets.MonthEnd(0)
        result_df['YearPeriod'] = result_df['CalendarYear/Month'].str[-4:] + result_df['CalendarYear/Month'].str[:2]

        # Connect to the database
        conn = sqlite3.connect(db_dir)
        cur = conn.cursor()

        # Check if the table exists
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='ExchangeRate'"
        cur.execute(query)
        result = cur.fetchone()

        # If table exists, delete rows with YearPeriod from periodList
        if result is not None:
            periodList = result_df['YearPeriod'].unique()
            cur.execute("DELETE FROM ExchangeRate WHERE \"YearPeriod\" IN (%s)" % ','.join(['?'] * len(periodList)), periodList)
            conn.commit()

        # Insert the data into the database
        result_df.to_sql('ExchangeRate', conn, if_exists='append', index=False)
        conn.close()

        logger.info(f"Data loaded into database {db_dir}")
    except Exception as e:
        logger.error(f"Failed to load exchange rates into {db_dir}. Error: {e}")
        return e