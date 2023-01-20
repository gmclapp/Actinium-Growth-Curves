import datetime as dt
import pandas as pd
from exceptions import *



def parse_dates(DF, date_col, time_col):
    new_series = []
    
    for i,row in DF.iterrows():
        new_datetime = parse_date(row[date_col],row[time_col])
        new_series.append(new_datetime)

    return(pd.Series(new_series))
           
def parse_date(date, time):
    try:
        m,D,Y = date.split("/")
        H,M = time.split(":")
        return(dt.datetime(int(Y),int(m),int(D),int(H),int(M)))
    except:
        append_to_log("Failed to parse date. Expected a date and time, received: {} {}".format(date, time))

def append_to_log(message):
    with open("log.txt",mode='a') as f:
        today = dt.datetime.today()
        f.write("{}: {}\n".format(today,message))

def error_check_source(file):
    '''Takes a file path and detects whether the datetime data is appropriately
    sorted from oldest to newest.'''
    try:
        DF = pd.read_csv(file,parse_dates=True)
        
    except FileNotFoundError:
        # I don't we can ever get here without already raising this exception...
        raise FileNotFoundError

    print(DF.head())
    raise BadDatesError

##    DF["Date and Time"] = parse_dates(DF,"Date","Time")
    # if dates are in the wrong order
    # raise exception
    
