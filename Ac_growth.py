''' Python Plotting Template
 Current maintainer: Glenn Clapp
 Last modified: 20 January 2023

 Contributions from
 Austin Czyzewski through
 23 April 2022

 Based on work by
 Chad Denbrock
 December 2020
 
 Niowave, Inc.
 '''
# ------------------- L I B R A R Y   I M P O R T S ------------------------- #

import random
from matplotlib import pyplot as plt
from matplotlib import transforms  
import matplotlib 
import numpy as np 
from scipy import interpolate
import datetime as DT
from matplotlib.dates import DateFormatter
import pandas as pd
import json
import warnings
warnings.filterwarnings("ignore", message="FixedFormatter should only be used together with FixedLocator")
import tkinter as tk
import os
from utils import *
from exceptions import *

# ------------------- P L O T   S E T T I N G S  ---------------------------- #

matplotlib.rcParams['savefig.dpi']  = 300
matplotlib.rcParams['font.size']    = 16
matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

# ------------------ H E L P E R  F U N C T I O N S ------------------------- #
class errorCode():
    def __init__(self):
        self.code = 0
        self.codes = {0:"Normal",
                      1:"Bad irradiation log.",
                      2:"Beam energy out of range.",
                      3:"Empty irradiation log.",
                      4:"Dates out of order in source file.",
                      5:"Source data not found.",
                      6:"Unhandled exception"}

    def check(self,new):
        try:
            self.codes[new]
            return(True)
        except KeyError:
            appen_to_log("Error code not found in code dict.")
            return(False)
        
    def set(self,new):
        if self.check(new):
            self.code = new
        else:
            pass

    def get(self):
        return(self.code)
    def get_txt(self):
        return(self.codes[self.code])
        
def parse_6dig_date(date):
    day = DT.datetime.strptime(date, '%y%m%d').day
    month = DT.datetime.strptime(date, '%y%m%d').month
    year = DT.datetime.strptime(date, '%y%m%d').year
    return(DT.datetime(year,month,day))
    
def calculate_delta(df):
    delta = []
    for i,t in enumerate(df["Elapsed time (s)"]):
        if i==0:
            delta.append(df["Elapsed time (s)"][0])
        else:
            delta.append(t-df["Elapsed time (s)"][i-1])

    df["dt (s)"] = delta
    
def reaction_calculator(df,ra_225_init,ac_225_init,Reaction_Rate_Modification_Factor):
    '''Takes a data frame with "Integrated Power (kWhr from Acc)", "dt (s)",
    "Energy (MeV)", and "Radium target mass (g)" columns and appends "power",
    "electrons", "reaction rate per gram", "reactions per second", "Radium-225",
    "Actinium-225", "Radium-225 Activity (mCi)", and "Actinium-225 Activity (mCi)"
    '''

    # ------------------- D E C A Y   R A T E S  ---------------------------- #
    ac_225_hl = 8.57e5 # 9.9 days
    ra_225_hl = 1.29e6 # 14.9 days

    ac_225_l = np.log(2)/ac_225_hl
    ra_225_l = np.log(2)/ra_225_hl
    
    df["power"] = df["Integrated Power (kWhr from Acc)"] / (df["dt (s)"] / 3600)*1000
    df["electrons"] = df["power"]/(df["Energy (MeV)"]* 1e6 * 1.6e-19)
    df["reaction rate per gram"] = reaction_rate_calculator(df["Energy (MeV)"],Reaction_Rate_Modification_Factor)
    df["reactions per second"] = df["reaction rate per gram"] * df["Radium target mass (g)"] * df["electrons"]

    Ra225 = []
    Ac225 = []
    
    for i,row in df.iterrows():
        if i > 0:
            R = row["reactions per second"]
            Ra225decays = ra_225_l*Ra225[-1]
            Ra225.append(Ra225[-1] + (R-Ra225decays)*row["dt (s)"])
            Ac225decays = ac_225_l * Ac225[-1]
            try:
                if row['Extraction'].lower() == 'yes':
                    Ac225.append(0)
                else:
                    Ac225.append(Ac225[-1] + (Ra225decays - Ac225decays)*row["dt (s)"])
            except:
                Ac225.append(Ac225[-1] + (Ra225decays - Ac225decays)*row["dt (s)"])
                
            else:
                pass
        else:
            Ra225.append(ra_225_init)
            Ac225.append(ac_225_init)            
            
    df["Radium-225"] = Ra225
    df["Actinium-225"] = Ac225
    df["Radium-225 Activity (mCi)"] = df["Radium-225"] * ra_225_l / 3.7e7
    df["Actinium-225 Activity (mCi)"] = df["Actinium-225"] * ac_225_l / 3.7e7
        
    df.reset_index()
    
def reaction_rate_calculator(energy,Reaction_Rate_Modification_Factor):
    '''Reaction rates given in rxns/g/e for Green Curve Geometry at 10 ml
    flat RaT solution volume'''
    # energy_list         = [10.0,        11.0,       12.0,       13.0,       14.0,       15.0]
    energy_list         = [9,10,11,12,13,14,15,16,17,18,19,20]
    # reaction_rate_list  = [9.970e-7,    2.058e-6,   3.862e-6,   6.494e-6,   9.636e-6,   1.283e-5]
    reaction_rate_list  = [1.506e-7,3.412e-7,6.668e-7,1.206e-6,1.982e-6,\
                           2.909e-6,3.872e-6,4.810e-6,5.752e-6,6.621e-6,\
                           7.450e-6,8.315e-6]
        
    reaction_rate_list = [original * Reaction_Rate_Modification_Factor for original in reaction_rate_list]

    interpolate_func    = interpolate.interp1d(energy_list,reaction_rate_list)
    reaction_rate       = interpolate_func(energy)
    return (reaction_rate)


def dose_to_accumulated_power(dose,mGy_min_watt):
    '''takes a dose measurement in Gy and estimates an integrated power in kWhr
    required to produce that dose. Based on historical measurements.'''
    return dose/mGy_min_watt/60

def power_to_integrated_power(power,dt):
    '''takes power in W and dt in seconds and returns kwHr of integrated power'''
    return(power/1000*dt/3600)

def createPowerProjection(df,Schedule,mean_power,std_power,stds_from_avg,include_schedule=False):
    '''Takes a mean power from historical data, a standard deviation of power
    from historical data and populates the integrated power column of the given
    data frame'''
    try:
        SchDF = pd.read_csv(Schedule)
    except FileNotFoundError:
        append_to_log("Schedule file not found.")
        SchDF = pd.DataFrame(columns=["Start date",
                                      "Start time",
                                      "End date",
                                      "End time",
                                      "Extraction",
                                      "Target mass addition"])
        
    SchDF["Start date and time"] = parse_dates(SchDF,"Start date","Start time")
    SchDF["End date and time"] = parse_dates(SchDF,"End date","End time")

    sims = []
    for i in range(500):
        power = []
        extraction = []
        for d in df["Date and Time"]:
            down=False
            ex=False
            for i,row in SchDF.iterrows():
                if row["Start date and time"] < d <= row["End date and time"]:
                    down = True
                    new_power = 0
                    if row["Extraction"] == "YES":
                        ex=True
                    break

            if down:
                new_power = 0
                if ex:
                    extraction.append("YES")
                else:
                    extraction.append("NO")      
            else:
                new_power = -1
                while new_power < 0:
                    new_power = random.normalvariate(mean_power,std_power)
                extraction.append("NO")
                
                    
            power.append(new_power)
        sims.append(power)
    tempDF = pd.DataFrame(sims)

    mean_power = []
    upper_power = []
    lower_power = []
    for col in tempDF:
        mean = tempDF[col].mean()
        sd = tempDF[col].std()
        
        mean_power.append(mean)
        upper_power.append(mean+stds_from_avg*sd)

        lower = mean-stds_from_avg*sd
        if lower > 0:
            lower_power.append(lower)
        else:
            lower_power.append(0)
        

    return(upper_power,mean_power,lower_power,extraction)

def find_regression(dfMeas, df):
    '''takes two dataframes, the first with activity measurements of the target,
    the second with predicted data using the model and uses these data to find
    a regression statistic.'''
    dfMeas["Date and Time"] = parse_dates(dfMeas,"Date","Time")
    regressions = []
    ybar = dfMeas["Ac-225"].mean()
    SSreg = 0
    SStot = 0
    SSres = 0
    for i, row in dfMeas.iterrows():
        for j, jow in df.iterrows():
            if jow["Date and Time"]>row["Date and Time"]:
                print("Found the next date!")
                y1 = df.at[j-1,"Actinium-225 Activity (mCi)"]
                x1 = df.at[j-1,"Date and Time"]
                y2 = df.at[j,"Actinium-225 Activity (mCi)"]
                x2 = df.at[j,"Date and Time"]
                yhat = row["Ac-225"]
                x = row["Date and Time"]

                dy = y2-y1
                dx = (x2-x1).total_seconds()
                try:
                    rate = dy/dx
                except ZeroDivisionError:
                    append_to_log("Failed to find regression, dx is zero for some reason")
                    return()

                y = (x-x1).total_seconds() * rate + y1
                SSreg += (yhat-ybar)**2
                SStot += (y-ybar)**2
                SSres += (y-yhat)**2
                break
    if SStot != 0:
        Rsqr = 1 - (SSreg/SStot)
        return(Rsqr)
    elif SStot == 0:
        append_to_log("SStot = 0, there is no variability in the irradiation data!")
        return(0.0)

def scale_power(df, dfpower):
    dfpower["Start Date and Time"] = parse_dates(dfpower,"Start date","Start time")
    dfpower["End Date and Time"] = parse_dates(dfpower,"End date","End time")
    
    for i,row in df.iterrows():
        for j,jow in dfpower.iterrows():
            start = jow["Start Date and Time"].to_pydatetime()
            end = jow["End Date and Time"].to_pydatetime()
            if start < row["Date and Time"].to_pydatetime() < end:
                df.at[i,"Integrated Power (kWhr from Acc)"] = df.at[i,"Integrated Power (kWhr from Acc)"]*jow["Scalar"]
            else:
                pass
    
def Ac_growth(GUI_obj):
    errorCodeInst = errorCode()
    errorCodeInst.set(0)
    # ------------------- R E T R I E V E   D A T A  ---------------------------- #
    
    # Import data from file
    with open("Ac_growth_meta.txt","r") as f:
        meta = json.load(f)

    # ----------------- S C R I P T   S E T T I N G S  -------------------------- #

    # Error check source files
    try:
        error_check_source(GUI_obj.beamPath.get())
        error_check_source(GUI_obj.targetMeasPath.get())
        error_check_source(GUI_obj.downSchedPath.get())
        error_check_source(GUI_obj.powerSchedPath.get())

    except FileNotFoundError:
        errorCodeInst.set(5) # Source data not found

    except BadDatesError:
        errorCodeInst.set(4) # Bad dates found in source files
        
    except Exception as ex: # Make this specific to a custom error type
        errorCodeInst.set(6) # Unhandled exception
        print(ex)
        
    
    Adjustable_Ratio = meta["Adjustable ratio"]
    Reaction_Rate_Modification_Factor = meta["Reaction rate modification factor"]
    mGy_min_watt = meta["mGy per min per watt"]

    DF = pd.read_csv(GUI_obj.beamPath.get(),parse_dates=True)
    try:
        DFmeas = pd.read_csv(GUI_obj.targetMeasPath.get())
    except FileNotFoundError:
        append_to_log("Target measurements file not found.")
        DFmeas = pd.DataFrame(columns=["Date",
                                       "Time",
                                       "Ac-225"])

    DF["Date and Time"] = parse_dates(DF,"Date","Time")
    try:
        DF["Elapsed time (s)"] = (DF["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()
        calculate_delta(DF)
    except IndexError:
        errorCodeInst.set(3)
        return(errorCodeInst,0)

    # Create calculated data
    DF["Integrated Power (kWhr from Acc)"] = dose_to_accumulated_power(DF["Accumulated Dose"],
                                                                       mGy_min_watt)
    try:
        DFPowerScale = pd.read_csv(GUI_obj.powerSchedPath.get())
    except FileNotFoundError:
        append_to_log("Power scalar file not found.")
        DFPowerScale = pd.DataFrame(columns=["Start date",
                                             "Start time",
                                             "End date",
                                             "End time",
                                             "Scalar"])
    scale_power(DF,DFPowerScale)
    
    DF["Dose rate (Gy/s)"] = DF["Accumulated Dose"]/DF["dt (s)"]
    
    start_time = DF["Date and Time"][0].to_pydatetime()

    latest_time = DF["Date and Time"].tail(1).item().to_pydatetime()

    # ------------------------ Calculation Algorithm          ---------------- #
    ac_225_hl = 8.57e5 # 9.9 days
    ra_225_hl = 1.29e6 # 14.9 days

    ac_225_l = np.log(2)/ac_225_hl
    ra_225_l = np.log(2)/ra_225_hl
    
    initial_ra_225_N = GUI_obj.startRa.get() * 3.7e4 / ra_225_l
    initial_ac_225_N = GUI_obj.startAc.get() * 3.7e4 / ac_225_l

    try:
        reaction_calculator(DF,
                            initial_ra_225_N,
                            initial_ac_225_N,
                            Reaction_Rate_Modification_Factor)

        latest_Ac225 = DF["Actinium-225 Activity (mCi)"].tail(1).item()
        append_to_log("Total integrated beam power: {:4.2f} kWhr".format(DF["Integrated Power (kWhr from Acc)"].sum()))
        append_to_log("Activity of Ac-225 at the last reported time: {:4.3f} mCi".format(latest_Ac225))
        
    except TypeError:
        append_to_log("Reaction calculator failed incorrect, data type encountered in irradiation log.")
        errorCodeInst.set(1)
        return(errorCodeInst,0)
    except ValueError:
        append_to_log("Reaction calculator failed, bad beam energy range.")
        errorCodeInst.set(2)
        return(errorCodeInst,0)
        
    if len(DF) >= 3:
        reg = find_regression(DFmeas,DF)
    else:
        append_to_log("Insufficient data points to calculate the coefficient of determination.")
 
    

    # ------------------------ Projection Algorithm          ---------------- #
    #######################
    # Projection settings #
    #######################

    mask = (DF['Extraction'] == 'NO')
    masked_df = DF[mask]

    Dose_mean = meta["Project dt (s)"]*masked_df["Dose rate (Gy/s)"].tail(meta["Moving avg length"]).mean()
    Dose_std = meta["Project dt (s)"]*masked_df["Dose rate (Gy/s)"].tail(meta["Moving avg length"]).std()

    Projected_power = dose_to_accumulated_power(Dose_mean,mGy_min_watt)
    Power_std = dose_to_accumulated_power(Dose_std,mGy_min_watt)
    
    End = DF["Date and Time"].tail(1).item().to_pydatetime() # Get the last date
    
    # Create a series of datetime objects with parameters from meta data for projection
    dates = [End + DT.timedelta(seconds=x*meta["Project dt (s)"]) for x in range(int(86400*meta["Project length (days)"]/meta["Project dt (s)"]))]

    #######################
    # Projections         #
    #######################
    DF_proj = pd.DataFrame(columns=masked_df.columns)
    DF_proj["Date and Time"] = dates
    upper, mean, lower, extraction = createPowerProjection(DF_proj,
                                                           GUI_obj.downSchedPath.get(),
                                                           Projected_power,
                                                           Power_std,
                                                           meta["Standard deviations from average"],
                                                           include_schedule=False)
    
    DF_proj["Energy (MeV)"] = float(meta["Project energy"])
    DF_proj["Radium target mass (g)"] = float(meta["Radium target mass (g)"])
    DF_proj["Elapsed time (s)"] = (DF_proj["Date and Time"] - DF["Date and Time"][0]).dt.total_seconds()
    calculate_delta(DF_proj)
    DF_proj["Extraction"] = extraction

    DF_custom = DF_proj.copy()
    DF_lower = DF_proj.copy()
    DF_upper = DF_proj.copy()
    
    DF_proj["Integrated Power (kWhr from Acc)"] = mean
    DF_lower["Integrated Power (kWhr from Acc)"] = lower
    DF_upper["Integrated Power (kWhr from Acc)"] = upper

    Interval = meta["Standard deviations from average"]*Power_std
                           
##    DF_custom["Integrated Power (kWhr from Acc)"] = meta["Custom projection power"]*(DF_custom["dt (s)"]/3600)/1000
    upper, mean, lower, extraction = createPowerProjection(DF_custom,
                                                           GUI_obj.downSchedPath.get(),
                                                           meta["Custom projection power"]*(meta["Project dt (s)"]/3600)/1000,
                                                           0,
                                                           meta["Standard deviations from average"],
                                                           include_schedule=False)
    DF_custom["Integrated Power (kWhr from Acc)"] = mean
    
    reaction_calculator(DF_proj,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_lower,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_upper,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    reaction_calculator(DF_custom,
                        DF.tail(1)["Radium-225"].item(),
                        DF.tail(1)["Actinium-225"].item(),
                        Reaction_Rate_Modification_Factor)

    try:
        DF.to_csv(os.path.join(GUI_obj.outputPath.get(),"output.csv"))
        DF_proj.to_csv(os.path.join(GUI_obj.outputPath.get(),"projection.csv"))
    except AttributeError:
        append_to_log("No output path provided. No projection csv will be created.")
        
    # ------------------- B E G I N   P L O T T I N G ---------------------------- #

    fig, ax = plt.subplots(1,1,figsize=(11,8.5)) 

    ax.plot(DF["Date and Time"], DF["Radium-225 Activity (mCi)"],'r')
    ax.plot(DF["Date and Time"], DF["Actinium-225 Activity (mCi)"],'g')
        
    # Plot projections
    ax.plot(DF_proj["Date and Time"], DF_proj["Radium-225 Activity (mCi)"],'r--')
    ax.plot(DF_proj["Date and Time"], DF_proj["Actinium-225 Activity (mCi)"],'g--')
    ax.plot(DF_custom["Date and Time"], DF_custom["Radium-225 Activity (mCi)"],'r:')
    ax.plot(DF_custom["Date and Time"], DF_custom["Actinium-225 Activity (mCi)"],'g:')


    ax.fill_between(DF_upper["Date and Time"],
                    DF_upper["Radium-225 Activity (mCi)"], DF_lower["Radium-225 Activity (mCi)"],
                    color='red',alpha=0.2)

    ax.fill_between(DF_upper["Date and Time"],
                    DF_upper["Actinium-225 Activity (mCi)"], DF_lower["Actinium-225 Activity (mCi)"],
                    color='green',alpha=0.2)


    # Plotting black dashed line at last reported data
    ylim    = (0,meta["plot y-scale"])
    xlim = (parse_6dig_date(meta["plot x min"]),parse_6dig_date(meta["plot x max"]))
    ax.plot([latest_time,latest_time],[ylim[0],ylim[1]],'k--')
    ax.set_ylim(0.0,ylim[1])
    ax.set_xlim(xlim[0],xlim[1])

    # Plot target measurements
    try:
        for index,pt in DFmeas.iterrows():
            m,d,y = pt["Date"].split("/")
            h,M = pt["Time"].split(":")
            date = DT.datetime(int(y),int(m),int(d),int(h),int(M))
            data = pt["Ac-225"]
            ax.plot(date,float(data),'kx',ms=10)
            ax.text(date,float(data),data,ha='right',va='center',fontsize = 10) 

    except:
        append_to_log("No target measurements to display")

    caption_text = "{:.3f}".format(latest_Ac225)
    ax.annotate(caption_text,xy = (latest_time,latest_Ac225),
                xytext = (20,-20),
                textcoords='offset points',
                arrowprops=dict(arrowstyle="->"),
                ha = 'left',
                va = 'center',
                fontsize = 16)
                
    ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, fontsize = 14);
    ax.set(
         title      = r'Niowave Production Milestones $^{225}$Ac Campaign',
         ylabel     = r'Activity (mCi)',
         ylim       = ylim,
         yscale     = 'linear'
    )
    date_form = DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(date_form)

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(3))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))
    ax2 = ax.twinx()
    ax2.set_ylim(ylim)
    ax2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(5))

    ax.yaxis.grid(True, which = 'major')
    ax.xaxis.grid(True, which = 'major')
    ax.yaxis.grid(True, which = 'minor', alpha = 0.25)
    ax.xaxis.grid(True, which = 'minor', alpha = 0.25)
    legend_list = [r'$^{225}$Ra',r'$^{225}$Ac']
    ax.legend(legend_list,loc = 'upper left')

    # Add caption below xlabel
    caption_text = ("The black dotted line shows the date of the most recent irradiation data. \n\
    Assumptions for projection: {:2.0f} mg RaT, {:3.0f} +/- {:3.0f} W and {:3.0f} W with proper beam steering.".format(1000*meta["Radium target mass (g)"],
                                                                                                                                      Projected_power*1000,
                                                                                                                                      Interval*1000,
                                                                                                                                      meta["Custom projection power"]))
    trans = transforms.blended_transform_factory(
         ax.transAxes, fig.transFigure
    )              # Makes x axis 'axes' coordinates and y axis 'figure' coordinates
    ax.text(0.5, 0.03, caption_text, ha = 'center', va = 'top', fontsize = 12, transform = trans)
    if End > DT.datetime.today():
        ax.text(0,0,"Caution: Plot contains speculative data.",ha='center',va='top',fontsize=12,transform=trans)

    # Add current date to upper right corner of plot

    date_string = DT.date.today().strftime('%B %d, %Y')
    ax.text(1.00,1.001,date_string,fontsize = 8, ha = 'right', va = 'bottom', transform = ax.transAxes)

    # Save figure as a png
    date_string_2   = DT.date.today().strftime('%Y%m%d')
    file_name = f'{date_string_2}_ac_225_growth_curve.png'
    try:
        plt.savefig(os.path.join(GUI_obj.outputPath.get(),file_name), bbox_inches = 'tight')
        
        plt.savefig(os.path.join(GUI_obj.outputPath.get(),"current_ac_225_growth_curve.png"))
    except AttributeError:
        append_to_log("No output path provided. No activity figures will be saved.")

    # ------------------- P O W E R   P L O T T I N G ---------------------------- #

    fig, ax = plt.subplots(1,1,figsize=(11,8.5))
        
    ax.plot(DF["Date and Time"],DF["power"])

    ylim = (0.0,ax.get_ylim()[1])

    ax.set_xticklabels(ax.get_xticklabels(), rotation = 45, fontsize = 16);
    ax.set(
         title      = r'Niowave R&D milestones $^{225}$Ac Campaign - Beam Power',
         ylabel     = r'Power ("Chad Watts")',
         ylim       = ylim,
         yscale     = 'linear'
    )
    date_form = DateFormatter("%m/%d")
    ax.xaxis.set_major_formatter(date_form)

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))
    ax2 = ax.twinx()
    ax2.set_ylim(ylim)
    ax2.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(2))

    ax.yaxis.grid(True, which = 'major')
    ax.xaxis.grid(True, which = 'major')
    ax.yaxis.grid(True, which = 'minor', alpha = 0.25)
    ax.xaxis.grid(True, which = 'minor', alpha = 0.25)

    # Add caption below xlabel
    trans = transforms.blended_transform_factory(
         ax.transAxes, fig.transFigure
    )              # Makes x axis 'axes' coordinates and y axis 'figure' coordinates

    # Add current date to upper right corner of plot
    date_string = DT.date.today().strftime('%B %d, %Y')
    ax.text(1.00,1.001,date_string,fontsize = 8, ha = 'right', va = 'bottom', transform = ax.transAxes)


    # Save figure as a png
    date_string_2   = DT.date.today().strftime('%Y%m%d')
    file_name = f'{date_string_2}_ac_225_growth_curve_power.png'
    try:
        plt.savefig(os.path.join(GUI_obj.outputPath.get(),file_name),bbox_inches='tight')

    except AttributeError:
        append_to_log("No output path provided. No power figures will be saved.")
    try:
        return(errorCodeInst, reg)
    except UnboundLocalError:
        if len(DF) < 3:
            append_to_log("Insufficient data to generate regression model. Failed to return Rsqr.")            
        else:
            append_to_log("Unknown exception. Failed to return Rsqr.")

class dummy_GUI:
    def __init__(self):
        root = tk.Tk()
        self.beamPath = tk.StringVar(value=r"C:\Users\clapp\Desktop\Ac Growth data/irradiation log.csv")
        self.targetMeasPath = tk.StringVar(value=r"C:\Users\clapp\Desktop\Ac Growth data/Target measurements.csv")
        self.downSchedPath = tk.StringVar(value=r"C:\Users\clapp\Desktop\Ac Growth data/Schedule.csv")
        self.powerSchedPath = tk.StringVar(value=r"C:\Users\clapp\Desktop\Ac Growth data/Regression testing.csv")
        self.startRa = tk.DoubleVar(value=0)
        self.startAc = tk.DoubleVar(value=0)
        
__version__ = "1.0.0"
if __name__ == '__main__':
    GUI = dummy_GUI()
    errorCode, Rsqr = Ac_growth(dummy_GUI())
    print("Rsqr = {:4.2f}".format(Rsqr))
