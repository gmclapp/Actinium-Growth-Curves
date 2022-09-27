import tkinter as tk
from tkinter.filedialog import askopenfile, asksaveasfilename
from tkinter import ttk, TclError
import os
from datetime import datetime
from Ac_growth import *
import json

def append_to_log(message):
    with open("log.txt",mode='a') as f:
        today = datetime.today()
        f.write("{}: {}\n".format(today,message))

class error_popup:
    def __init__(self,parent,error):
        self.parent = parent
        self.error = error
        self.badchild = tk.Toplevel(self.parent.master)
        self.badchild.geometry("250x75")
        self.badchild.title("Error: \n{}".format(error))

        self.badchild.grid_columnconfigure(0,weight=1)
        
        # create elements
        Error_msg = ttk.Label(self.badchild,text=error)
        AckPB = ttk.Button(self.badchild,text="OK",command=self.acknowledge_error)
        
        # place elements
        Error_msg.grid(column=0,row=0)
        AckPB.grid(column=0,row=1)
        self.badchild.attributes('-topmost',True)
        append_to_log(error)

    def acknowledge_error(self):
        append_to_log("Error: {} acknowledged by user".format(self.error))
        self.badchild.destroy()
        
        
class dir_popup:
    def __init__(self,parent):
        self.parent = parent
        self.child = tk.Toplevel(self.parent.master)
        self.child.title("Directory selector")
        

        # Frame creation
        self.dir_frame()

        # Frame placement
        self.dirFR.grid(row=0,column=0,padx=2,pady=2)
        append_to_log("Directory selection dialog opened")
        
    def dir_cmd(self):
        self.parent.beamPath.set(askopenfile().name)
        append_to_log("Beam path set to {}".format(self.parent.beamPath.get()))

        # Open the data base and retrieve recent data for form autofill
        self.parent.get_last_data(self.parent.beamPath.get())
        self.child.attributes('-topmost',True)
        
    def target_cmd(self):
        self.parent.targetMeasPath.set(askopenfile().name)
        append_to_log("Target measurement path set to {}".format(self.parent.targetMeasPath.get()))
        self.child.attributes('-topmost',True)
        
    def sch_cmd(self):
        self.parent.downSchedPath.set(askopenfile().name)
        append_to_log("Downtime schedule path set to {}".format(self.parent.downSchedPath.get()))
        self.child.attributes('-topmost',True)

    def pow_cmd(self):
        self.parent.powerSchedPath.set(askopenfile().name)
        append_to_log("Power scalar path set to {}".format(self.parent.powerSchedPath.get()))
        self.child.attributes('-topmost',True)

    def new_beam_data_cmd(self):
        pathstr = None
        pathstr = asksaveasfilename(defaultextension=".csv")
        if pathstr:
            temp = pd.DataFrame(columns=["Date",
                                         "Time",
                                         "Energy (MeV)",
                                         "Accumulated Dose",
                                         "Pressure",
                                         "Radium target mass (g)",
                                         "Extraction"])
            temp.to_csv(pathstr,index=False)
            self.parent.beamPath.set(pathstr)
            append_to_log("Created beam data file {} and set as beam path".format(pathstr))
        
    def new_sched_data_cmd(self):
        pathstr = None
        pathstr = asksaveasfilename(defaultextension=".csv")
        if pathstr:
            temp = pd.DataFrame(columns=["Start date",
                                         "Start time",
                                         "End date",
                                         "End time",
                                         "Extraction",
                                         "Target mass addition"])
            temp.to_csv(pathstr,index=False)
            self.parent.downSchedPath.set(pathstr)
            append_to_log("Created downtime schedule data file {} and set as downtime schedule path".format(pathstr))
            
    def new_target_data_cmd(self):
        pathstr = None
        pathstr = asksaveasfilename(defaultextension=".csv")
        if pathstr:
            temp = pd.DataFrame(columns=["Date",
                                         "Time",
                                         "Ac-225"])
            temp.to_csv(pathstr,index=False)
            self.parent.targetMeasPath.set(pathstr)
            append_to_log("Created target measurement data file {} and set as target measurement path".format(pathstr))
            
    def new_power_sched_data_cmd(self):
        pathstr = None
        pathstr = asksaveasfilename(defaultextension=".csv")
        if pathstr:
            temp = pd.DataFrame(columns=["Start date",
                                         "Start time",
                                         "End date",
                                         "End time",
                                         "Scalar"])
            temp.to_csv(pathstr,index=False)
            self.parent.powerSchedPath.set(pathstr)
            append_to_log("Created power scalar schedule data file {} and set as power scalar schedule path".format(pathstr))

# ------------------- L A B E L   F R A M E   S E T U P S ------------------- #
    def dir_frame(self):
        self.dirFR = tk.LabelFrame(self.child,
                                   text="Data sources")
        
        beamDataPB = ttk.Button(self.dirFR,text="Select Beam Data",width=25,command=self.dir_cmd)
        newBeamDataPB = ttk.Button(self.dirFR,text="New",command=self.new_beam_data_cmd)
        
        targetPB = ttk.Button(self.dirFR,text="Select Target Data",width=25,command=self.target_cmd)
        newTargetDataPB = ttk.Button(self.dirFR,text="New",command=self.new_target_data_cmd)
        
        schedPB = ttk.Button(self.dirFR,text="Select Schedule Data",width=25,command=self.sch_cmd)
        newSchedDataPB = ttk.Button(self.dirFR,text="New",command=self.new_sched_data_cmd)
        
        powerSchedPB = ttk.Button(self.dirFR,text="Select Power Scale Data",width=25,command=self.pow_cmd)
        newPowerSchedDataPB = ttk.Button(self.dirFR,text="New",command=self.new_power_sched_data_cmd)

        DonePB = ttk.Button(self.dirFR,text="Done",command=self.child.destroy)


        beamDataLabel = ttk.Label(self.dirFR,text="Select the csv file with irradiation data: ")
        schedLabel = ttk.Label(self.dirFR,text="Select the csv file with scheduled down time: ")
        targetLabel = ttk.Label(self.dirFR,text="Select the csv file with the target activity measurements: ")
        powerLabel = ttk.Label(self.dirFR,text="Select the csv file with the power scalars: ")

        beamDataLabel.grid(column=0,row=0)
        beamDataPB.grid(column=1,row=0,padx=2,pady=2)
        newBeamDataPB.grid(column=2,row=0,padx=2,pady=2)

        schedLabel.grid(column=0,row=1)
        schedPB.grid(column=1,row=1,padx=2,pady=2)
        newTargetDataPB.grid(column=2,row=1,padx=2,pady=2)
        
        targetLabel.grid(column=0,row=2)
        targetPB.grid(column=1,row=2,padx=2,pady=2)
        newSchedDataPB.grid(column=2,row=2,padx=2,pady=2)

        powerLabel.grid(column=0,row=3)
        powerSchedPB.grid(column=1,row=3,padx=2,pady=2)
        newPowerSchedDataPB.grid(column=2,row=3,padx=2,pady=2)

        DonePB.grid(column=0,row=4,columnspan=3)
        
class GUI:
    def __init__(self,master,version,mod_date):
        self.version = version
        self.mod_date = mod_date
        
        self.master = master

        # Get meta data
        with open ("Ac_growth_meta.txt","r") as f:
            meta = json.load(f)
            
        # GUI variable definitions
        self.date = tk.StringVar(value = datetime.today().strftime('%y%m%d'))
        self.hour = tk.StringVar(value="23") # If IntVar, leading zeroes are interpreted as octal numbers
        self.minute = tk.StringVar(value="59") # If IntVar, leading zeroes are interpreted as octal numbers
        self.dose = tk.DoubleVar()
        self.extraction = tk.BooleanVar(value=False)
        self.targetmass = tk.DoubleVar()
        self.energy  = tk.DoubleVar()
        self.beamPath = tk.StringVar()
        self.targetMeasPath = tk.StringVar()
        self.downSchedPath = tk.StringVar()
        self.powerSchedPath = tk.StringVar()
        self.last_data_datetime = tk.StringVar(value=" ")
        self.custom_power = tk.DoubleVar(value=meta["Custom projection power"])
        self.sim_length = tk.IntVar(value=meta["Project length (days)"])
        self.movingAvgLen = tk.IntVar(value=meta["Moving avg length"])
        self.ylim = tk.DoubleVar(value=meta["plot y-scale"])

        # Frame creation
        self.dir_frame()
        self.dose_frame()
        self.sim_frame()

        # Frame placement
        self.dirFR.grid(row=0,column=0,padx=2,pady=2)
        self.simFR.grid(row=1,column=0,padx=2,pady=2)
        self.doseFR.grid(row=2,column=0,padx=2,pady=2)  

        self.dirFR.grid_columnconfigure(1,weight=1)
        self.simFR.grid_columnconfigure(1,weight=1)
        self.doseFR.grid_columnconfigure(1,weight=1)
        
# --------------------- H E L P E R   F U N C T I O N S --------------------- #
    def get_last_data(self,path):
        try:
            df = pd.read_csv(path)
            last_line = df.tail(1)
            self.energy.set(last_line["Energy (MeV)"].item())
            self.targetmass.set(last_line["Radium target mass (g)"].item()*1000)
            last_date = parse_date(last_line["Date"].item(),
                                   last_line["Time"].item())
            
            last_time = last_line["Time"].item()
            last_str = "Last data point: "+last_date.strftime('%y%m%d')+" "+last_time
            self.last_data_datetime.set(last_str)
        except Exception as ex:
            error_popup(self.master,"Failed to retrieve last line\nException: {}".format(ex))
##            print("Failed to retrieve last line\nException: {}".format(ex))
##            print(last_line["Energy (MeV)"].item())

# ----------------- P U S H   B U T T O N   C O M M A N D S ----------------- #
    

    def report_cmd(self):
        append_to_log("Generating report")

        if self.beamPath.get()[-4:] != ".csv":
            error_popup(self.master,"Beam path selection is missing or invalid")
            return()
        elif self.targetMeasPath.get()[-4:] != ".csv":
            error_popup(self.master,"Target measurement path selection is missing or invalid")
            return()
        elif self.downSchedPath.get()[-4:] != ".csv":
            error_popup(self.master,"Downtime schedule path selection is missing or invalid")
            return()
        elif self.powerSchedPath.get()[-4:] != ".csv":
            error_popup(self.master,"Power scalar schedule path selection is missing or invalid")
            return()
            
        start = datetime.now()
        try:
            Ac_growth(self)
        except IndexError:
            testDF = pd.read_csv(self.beamPath.get())
            print(testDF)
            
        runtime = datetime.now()-start
        append_to_log("Report generation complete, run time: {:4.2f} seconds".format(runtime.total_seconds()))

    def submit_data_cmd(self):

        try:
            data_submission_error = False
            submit_day = datetime.strptime(self.date.get(), '%y%m%d').day
            submit_month = datetime.strptime(self.date.get(), '%y%m%d').month
            submit_year = datetime.strptime(self.date.get(), '%y%m%d').year
            
            submit_hour = str(self.hour.get()).zfill(2)

            if int(submit_hour) > 23:
                error_popup(self.master,"Hour must be between 0 and 23")
                data_submission_error = True

            
            submit_minute = str(self.minute.get()).zfill(2)
            if int(submit_minute) > 59 or int(submit_minute) < 0:
                error_popup(self.master,"Minute must be between 0 and 59")
                data_submission_error = True
                
            submit_energy = self.energy.get()
            if float(submit_energy)<0:
                error_popup(self.master,"Energy must be greater than 0 MeV")
                data_submission_error = True
                
            submit_dose = self.dose.get()
            if float(submit_dose)<0:
                error_popup(self.master,"Dose must be greater than 0 Gy")
                data_submission_error = True
                
            submit_target_mass = self.targetmass.get()/1000
            if float(submit_target_mass)<0:
                error_popup(self.master,"Target mass must be greater than 0mg")
                data_submission_error = True
                
            submit_extraction = ("YES" if self.extraction.get() == True else "NO")

            if not data_submission_error:
                try:
                    with open(self.beamPath.get(), 'a') as file:
##                        file.write(f"{submit_month}/{submit_day}/{submit_year} {submit_hour}:{submit_minute},")
                        file.write(f"{submit_month}/{submit_day}/{submit_year},")
                        file.write(f"{submit_hour}:{submit_minute},")
                        file.write(f"{submit_energy},{submit_dose},0,{submit_target_mass},")
                        file.write(f"{submit_extraction}\n")
                        
                    self.dose.set(0)
                    # Open the data base and retrieve recent data for form autofill
                    self.get_last_data(self.beamPath.get())
                    append_to_log("New datapoint submitted")
                except FileNotFoundError as ex:
                    error_popup(self.master,"You must first choose an irradiation log.")
                    append_to_log("A datapoint was not submitted because no irradiation log was chosen.")
            else:
                append_to_log("An error prevented a datapoint from being submitted.")
        except TclError as ex:
            error_popup(self.master,"Invalid data point entry: {}".format(ex))
            append_to_log("An error prevented a datapoint from being submitted.")
            
    def apply_sim_settings(self):
        with open ("Ac_growth_meta.txt","r") as f:
            meta = json.load(f)
        with open ("Ac_growth_meta.txt","w") as f:
            meta["Custom projection power"] = self.custom_power.get()
            meta["Project length (days)"] = self.sim_length.get()
            meta["Moving avg length"] = self.movingAvgLen.get()
            meta["plot y-scale"] = self.ylim.get()
            
            json.dump(meta,f,indent=4)
        append_to_log("Meta data settings saved")

    def open_directory_popup(self):
        child = dir_popup(self)
    
# ------------------- L A B E L   F R A M E   S E T U P S ------------------- #
    def dir_frame(self):
        self.dirFR = tk.LabelFrame(self.master,
                                   text="Reporting",
                                   width=250)

        # Create elements
        self.beamdirLabel = ttk.Label(self.dirFR,
                                      text="Choose data sources")
        self.ask_filePB = ttk.Button(self.dirFR,
                                     text="Choose",
                                     command=self.open_directory_popup)
        self.reportPB = ttk.Button(self.dirFR,
                                   text="Create Report",
                                   command=self.report_cmd)

        # Place elements
        self.beamdirLabel.grid(column=0,row=0)
        self.ask_filePB.grid(column=1,row=0,padx=2,pady=2)
        self.reportPB.grid(column=2,row=0,padx=2,pady=2)

    def sim_frame(self):
        self.simFR = tk.LabelFrame(self.master,
                                   text="Simulation settings",
                                   width=250)

        # Create elements
        self.customPowerLabel = ttk.Label(self.simFR,
                                          text="Enter custom power in Watts")
        self.customPowerEntry = ttk.Entry(self.simFR,
                                          textvariable=self.custom_power)
        self.simLengthLabel = ttk.Label(self.simFR,
                                        text="Enter the length of the simulation in days")
        self.simLengthEntry = ttk.Entry(self.simFR,
                                        textvariable=self.sim_length)
        self.movingAvgLenLabel = ttk.Label(self.simFR,
                                           text="Enter the length of the moving average in data points")

        self.movingAvgLenEntry = ttk.Entry(self.simFR,
                                           textvariable=self.movingAvgLen)

        self.ylimLabel = ttk.Label(self.simFR,
                                   text="Enter the upper limit of the y axis in mCi")
        self.ylimEntry = ttk.Entry(self.simFR,
                                   textvariable=self.ylim)
        
        self.applyPB = ttk.Button(self.simFR,
                                  text="Apply",
                                  command=self.apply_sim_settings)
        

        # Place elements
        self.customPowerLabel.grid(column=0,row=0,padx=2,pady=2)
        self.customPowerEntry.grid(column=1,row=0,padx=2,pady=2)

        self.simLengthLabel.grid(column=0,row=1,padx=2,pady=2)
        self.simLengthEntry.grid(column=1,row=1,padx=2,pady=2)

        self.movingAvgLenLabel.grid(column=0,row=2,padx=2,pady=2)
        self.movingAvgLenEntry.grid(column=1,row=2,padx=2,pady=2)

        self.ylimLabel.grid(column=0,row=3,padx=2,pady=2)
        self.ylimEntry.grid(column=1,row=3,padx=2,pady=2)

        self.applyPB.grid(column=0,row=4,padx=2,pady=2)
        
    def dose_frame(self):
        # Create elements
        self.doseFR = tk.LabelFrame(self.master,
                                    text="Dose data entry",
                                    width=250)

        self.last_data_label = ttk.Label(self.doseFR,
                                         textvariable=self.last_data_datetime)
        
        self.end_time_label = ttk.Label(self.doseFR,
                                        text="End time (24hr format)")
        
        self.date_label = ttk.Label(self.doseFR,
                                    text = "Date (YYMMDD)")
        self.dateEntry = ttk.Entry(self.doseFR, 
                                   textvariable=self.date)
        
        self.hourEntry = ttk.Entry(self.doseFR,
                                   textvariable=self.hour)
        self.colon_label = ttk.Label(self.doseFR,
                                     text=":")
        self.minEntry = ttk.Entry(self.doseFR,
                                  textvariable=self.minute)
        
        self.dose_label = ttk.Label(self.doseFR,
                                    text="Dose (Gy)")
        self.doseEntry = ttk.Entry(self.doseFR,
                                   textvariable=self.dose)
        
        self.extraction_label = ttk.Label(self.doseFR,
                                          text="Ac-225 extraction")
        self.extractionCB = ttk.Checkbutton(self.doseFR,
                                         variable=self.extraction)
        
        self.target_mass_label = ttk.Label(self.doseFR,
                                           text="Target mass (mg)")
        self.targetEntry = ttk.Entry(self.doseFR,
                                     textvariable=self.targetmass)
        
        self.energy_label = ttk.Label(self.doseFR,
                                      text = "Beam Energy (MeV)")
        self.energyEntry = ttk.Entry(self.doseFR,
                                     textvariable = self.energy)
        
        self.submitPB = ttk.Button(self.doseFR,
                                   text="Submit",
                                   command=self.submit_data_cmd)

        # Place elements
        self.last_data_label.grid(column=0, row=0)
        self.date_label.grid(column=0, row=1)
        self.dateEntry.grid(column=1, row=1)
        
        self.end_time_label.grid(column=0,row=2)
        self.hourEntry.grid(column=1, row=2)
        self.colon_label.grid(column=2,row=2)
        self.minEntry.grid(column=3,row=2)
        
        
        self.dose_label.grid(column=0,row=3)
        self.doseEntry.grid(column=1,row=3)
        
        self.extraction_label.grid(column=0,row=4)
        self.extractionCB.grid(column=1,row=4)
        
        self.target_mass_label.grid(column=0,row=5)
        self.targetEntry.grid(column=1,row=5)
        
        self.energy_label.grid(column=0, row=6)
        self.energyEntry.grid(column=1, row=6)
        
        self.submitPB.grid(column=0,row=7,columnspan=5)
        
if __name__ == '__main__':

    __version__ = "0.0.1"
    last_modified = "10-August-2022"

    root = tk.Tk()

    app = GUI(root,__version__,last_modified)
    try:
        root.mainloop()
    except Exception as ex:
        append_to_log("There was an unhandled exception and the program was forced to close")
    root.destroy()
