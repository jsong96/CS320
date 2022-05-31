# project: p4
# submitter: jsong99
# partner: None

import click
from zipfile import ZipFile
import zipfile
import csv
from io import TextIOWrapper 
import re
import ipaddress
from operator import itemgetter
import geopandas
from collections import defaultdict
import pandas as pd
from matplotlib.animation import FuncAnimation
from matplotlib.animation import Animation
from matplotlib.animation import FFMpegWriter
from matplotlib import pyplot as plt

# https://github.com/tylerharter/cs320/tree/master/s20/p4
def zip_csv_iter(name):
    with ZipFile(name) as zf:
        with zf.open(name.replace(".zip", ".csv")) as f:
            reader = csv.reader(TextIOWrapper(f))
            for row in reader:
                yield row
                
def write_to_zip(filename, datafile):
    zf = ZipFile(filename, 'w',compression= zipfile.ZIP_DEFLATED)
    zf.write(datafile)
                
@click.command()
@click.argument('input_zip')
@click.argument('output_zip')
@click.argument('stride', type=click.INT)
def sample(input_zip, output_zip, stride):
    reader = zip_csv_iter(input_zip)
    header = next(reader)
    rows = list(reader)
    
    with open(output_zip.replace(".zip",".csv"), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for i in range(0,len(rows),stride):
            writer.writerows([rows[i]])
    
    write_to_zip(output_zip, output_zip.replace(".zip",".csv"))
    
def compare(row):
    # ip address encoding
    # https://stackoverflow.com/questions/9590965/convert-an-ip-string-to-a-number-and-vice-versa
    sub = re.sub(r"[a-zA-Z]+$", "000", row[0])
    return int(ipaddress.ip_address(sub))

@click.command()
@click.argument('input_zip')
@click.argument('output_zip')
def sort(input_zip, output_zip):
    reader = zip_csv_iter(input_zip)
    header = next(reader)
    rows = list(reader)
    ip_idx = header.index("ip")
    
    # sort according to ip address
    rows.sort(key=compare)
    
    with open(output_zip.replace('.zip','.csv'), 'w') as f:
        writer = csv.writer(f)
        # include header
        writer.writerow(header)
        for row in rows:
            writer.writerows([row])
        
    write_to_zip(output_zip, output_zip.replace(".zip",".csv"))


@click.command()
@click.argument('input_zip')
@click.argument('output_zip')
def country(input_zip, output_zip):
    reader = zip_csv_iter(input_zip)
    header = next(reader)
    header += ['country']
    ip_idx = header.index("ip")
    rows = list(reader)
    
    with ZipFile('IP2LOCATION-LITE-DB1.CSV.ZIP') as zf:
        with zf.open('IP2LOCATION-LITE-DB1.CSV') as f:
            
            dataset_reader = csv.reader(TextIOWrapper(f))
            data = list(dataset_reader)
            
            i = 0 
            j = 0
            while i < len(rows) and j < len(data):
                
                sub = re.sub(r"[a-zA-Z]+$", "000", rows[i][ip_idx])
                # 0(starting address) ~ 166275(ending address) country code, country fullname
                if int(ipaddress.ip_address(sub)) >= int(data[j][0]) and int(ipaddress.ip_address(sub)) <= int(data[j][1]):
                    rows[i].append(data[j][3])
                    i += 1
                    j += 1
                    
                else:
                    j += 1
    
    
    with open(output_zip.replace('.zip','.csv'), 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for row in rows:
            writer.writerows([row])
        
    write_to_zip(output_zip, output_zip.replace(".zip",".csv"))

def world():
    world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
    world.set_index("name", drop=False, inplace=True)
    return world[world["continent"] != "Antarctica"]

def plot_hour(zipname, hour=None, ax=None):
    reader = zip_csv_iter(zipname)
    header = next(reader)
    rows = list(reader)
    counts = defaultdict(int)
    country_idx = header.index("country")
    
    if hour is not None:
        time_idx = header.index('time')
        for row in rows:
            if int(row[time_idx].split(":")[0]) <= hour:
                counts[row[country_idx]] += 1
    else:
        for row in rows:
            counts[row[country_idx]] += 1

        
    world_df = world() 
    world_df["color"] = "0.7"
    
    for country, count in counts.items():
        if not country in world_df.index:
            continue
            
        color = "lightsalmon" # >= 1
        if count >= 10:
            color = "tomato"
        if count >= 100:
            color = "red"
        if count >= 1000:
            color = "brown"
        
        world_df.at[country, "color"] = color

    return world_df.plot(color=world_df["color"], legend=True, figsize=(16, 4))



@click.command()
@click.argument('input_zip')
@click.argument('output')
def geo(input_zip, output):
    ax = plot_hour(input_zip)
    ax.figure.savefig(output, bbox_inches="tight")

@click.command()
@click.argument('input_zip')
@click.argument('output_name')
@click.argument('hour', type=click.INT)
def geohour(input_zip, output_name, hour):
    ax = plot_hour(input_zip, hour)
    ax.figure.savefig(output_name, bbox_inches="tight")
    
@click.command()
@click.argument('input_zip')
@click.argument('video_name_html')
def video(input_zip, video_name_html):
    
    fig, ax = plt.subplots(figsize=(16,4))
    world_df = world() 
    world_df["color"] = "0.7"
    world_df.plot(color=world_df["color"], legend=True, ax = ax)
    
    reader = zip_csv_iter(input_zip)
    header = next(reader)
    rows = list(reader)
    country_idx = header.index("country")
    time_idx = header.index('time')
    counts = defaultdict(int)
    
    def helper(hour):
        time_idx = header.index('time')
        for row in rows:
            if int(row[time_idx].split(":")[0]) <= hour:
                counts[row[country_idx]] += 1
                
        for country, count in counts.items():
            if not country in world_df.index:
                continue

            color = "lightsalmon" # >= 1
            if count >= 10:
                color = "tomato"
            if count >= 100:
                color = "red"
            if count >= 1000:
                color = "brown"
            world_df.at[country, "color"] = color
            
        world_df.plot(color=world_df["color"], legend=True, ax=ax)
    
    anim = FuncAnimation(fig,helper,24,interval = 250)
    html = anim.to_html5_video()
    
    with open(video_name_html, "w") as f:
        f.write(html)
              
@click.group()
def commands():
    pass
            
commands.add_command(sample)
commands.add_command(sort)
commands.add_command(country)
commands.add_command(geo)
commands.add_command(geohour)
commands.add_command(video)

if __name__ == "__main__":
    commands()