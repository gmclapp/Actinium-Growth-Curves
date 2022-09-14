import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from scipy import stats

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
    timeframe = float(input("How long before and after conditioning should be considered? (hrs)\n>>> "))*3600
    
    DF = pd.read_csv("output.csv")
    DFCond = pd.read_csv("Conditioning times.csv")

    DF["Date and Time"] = parse_dates(DF,"Date","Time")
    DFCond["Date and Time"] = parse_dates(DFCond,"Date","Time")

    ax.plot(DF["Date and Time"],DF["power"])
    for i, row in DFCond.iterrows():
        ax.vlines(row["Date and Time"],0,300,linestyles='dashed',color='k')

    IterationB = []
    PowerB = []
    DTB = []

    IterationA = []
    PowerA = []
    DTA = []
    
    for i, row in DFCond.iterrows():
        for j, jow, in DF.iterrows():
            if 0 > (jow["Date and Time"] - row["Date and Time"]).total_seconds() > -timeframe:
                DTB.append(jow["Date and Time"].to_pydatetime())
                PowerB.append(jow["power"])
                IterationB.append(i)
            elif 0 < (jow["Date and Time"] - row["Date and Time"]).total_seconds() < timeframe:
                DTA.append(jow["Date and Time"].to_pydatetime())
                PowerA.append(jow["power"])
                IterationA.append(i)

    Before = pd.DataFrame()
    After = pd.DataFrame()
    
    Before["Date and Time"] = DTB
    Before["power (W)"] = PowerB
    Before["Iteration"] = IterationB

    After["Date and Time"] = DTA
    After["power (W)"] = PowerA
    After["Iteration"] = IterationA

    for i,row in Before.iterrows():
        try:
            ax.vlines(row["Date and Time"],0,300,colors='red',linestyles='dashed')
        except:
            continue

    for i,row in After.iterrows():
        try:
            ax.vlines(row["Date and Time"],0,300,colors='green',linestyles='dashed')
        except:
            continue

    paired_data =[]
    for i in range(len(DFCond["Date and Time"])):
        A = After.loc[After["Iteration"] == i]
        B = Before.loc[Before["Iteration"] == i]
        diff = A["power (W)"].mean() - B["power (W)"].mean()
        
        paired_data.append(diff)

    with open("paired t test.txt","w") as f:
        for d in paired_data:
            f.write(str(d)+"\n")
            
    tstat, pvalue = stats.ttest_1samp(paired_data,0)
    print("test statistic: {:4.2f}\np-value: {:4.3f}".format(tstat,pvalue))
    
    return(fig,ax)

if __name__ == "__main__":
    fig,ax = plt.subplots(1,1,figsize=(10,6))
    CavCondStudy(fig,ax)
    plt.show()
