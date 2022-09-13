import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

def parse_dates(DF, date_col, time_col):
    new_series = []
    
    for i,row in DF.iterrows():
        new_datetime = parse_date(row[date_col],row[time_col])
        new_series.append(new_datetime)

    return(pd.Series(new_series))

def parse_date(date, time):
    try:
        m,D,Y = date.split("/")
    except Exception as ex:
        print("Failed to parse date", ex)
        return()
    try:
        H,M = time.split(":")
        return(dt.datetime(int(Y),int(m),int(D),int(H),int(M)))
    except Exception as ex:
        print("Failed to parse time.",ex)

def CavCondStudy(fig,ax):
    DF = pd.read_csv("output.csv")
    DFCond = pd.read_csv("Conditioning times.csv")

    DF["Date and Time"] = parse_dates(DF,"Date","Time")
    DFCond["Date and Time"] = parse_dates(DFCond,"Date","Time")

    ax.plot(DF["Date and Time"],DF["power"])
    print(DF["power"].head())
    return(fig,ax)

if __name__ == "__main__":
    fig,ax = plt.subplots(1,1,figsize=(10,6))
    CavCondStudy(fig,ax)
    plt.show()
