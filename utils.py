from datetime import datetime

def append_to_log(message):
    with open("log.txt",mode='a') as f:
        today = datetime.today()
        f.write("{}: {}\n".format(today,message))
