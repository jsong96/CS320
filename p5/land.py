# project: p5
# submitter: jsong99
# partner: None

import zipfile
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import io
import matplotlib.pyplot as plt 
import math
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.animation import Animation
from matplotlib.animation import FFMpegWriter

def open(name):
    return Connection(name)

class Connection:
    def __init__(self, name):
        # save zipname and open database and zipfile
        self.name = name
        self.db = sqlite3.connect(name+".db")
        self.zf = zipfile.ZipFile(name+".zip")
        
        
        # extract information about all the sample files
        self.samp_list = {}
        query = "SELECT place_id, name, lat FROM places WHERE name LIKE 'samp%'"
        cur = self.db.cursor()
        cur.execute(query)
        samps = cur.fetchall()
        
        for samp in samps:
            self.samp_list[samp[0]] = samp[2]
            
        query = "SELECT place_id, image FROM images"
        cur = self.db.cursor()
        cur.execute(query)
        imges = cur.fetchall()
        
        key = self.samp_list.keys()
        
        self.images_list = {}
        
        for im in imges:
            if im[0] in key:
                self.images_list[im[0]] = im[1]
            
        self.combined_samp = {}
        
        for k in self.samp_list.keys():
            self.combined_samp[self.images_list[k]] = self.samp_list[k]
        
        query = "SELECT place_id, name, lat FROM places WHERE name NOT LIKE 'samp%'"
        cur = self.db.cursor()
        cur.execute(query)
        self.cities = cur.fetchall()
    
        # for coloring plot 
        use_cmap = np.zeros(shape=(256,4))
        use_cmap[:,-1] = 1
        uses = np.array([
            [0, 0.00000000000, 0.00000000000, 0.00000000000],
            [11, 0.27843137255, 0.41960784314, 0.62745098039],
            [12, 0.81960784314, 0.86666666667, 0.97647058824],
            [21, 0.86666666667, 0.78823529412, 0.78823529412],
            [22, 0.84705882353, 0.57647058824, 0.50980392157],
            [23, 0.92941176471, 0.00000000000, 0.00000000000],
            [24, 0.66666666667, 0.00000000000, 0.00000000000],
            [31, 0.69803921569, 0.67843137255, 0.63921568628],
            [41, 0.40784313726, 0.66666666667, 0.38823529412],
            [42, 0.10980392157, 0.38823529412, 0.18823529412],
            [43, 0.70980392157, 0.78823529412, 0.55686274510],
            [51, 0.64705882353, 0.54901960784, 0.18823529412],
            [52, 0.80000000000, 0.72941176471, 0.48627450980],
            [71, 0.88627450980, 0.88627450980, 0.75686274510],
            [72, 0.78823529412, 0.78823529412, 0.46666666667],
            [73, 0.60000000000, 0.75686274510, 0.27843137255],
            [74, 0.46666666667, 0.67843137255, 0.57647058824],
            [81, 0.85882352941, 0.84705882353, 0.23921568628],
            [82, 0.66666666667, 0.43921568628, 0.15686274510],
            [90, 0.72941176471, 0.84705882353, 0.91764705882],
            [95, 0.43921568628, 0.63921568628, 0.72941176471],
        ])
        for row in uses:
            use_cmap[int(row[0]),:-1] = row[1:]
        self.use_cmap = ListedColormap(use_cmap)
        
        
    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
    
    def close(self):
        self.db.close()
        self.zf.close()
    
    def list_images(self):
        file_list = self.zf.namelist()
        file_list.sort()
        return file_list
    
    def image_year(self, np_array):
        query = "SELECT * FROM images where image = '{}'".format(np_array)
        cur = self.db.cursor()
        cur.execute(query)
        year = cur.fetchone()[0]
        return year
    
    def image_name(self, np_array):

        query = "SELECT place_id FROM images where image='{}'".format(np_array)
        cur = self.db.cursor()
        
        cur.execute(query)
        place_id = cur.fetchone()[0]

        query_two = "SELECT name FROM places where place_id={}".format(place_id)
        cur.execute(query_two)
        name = cur.fetchone()[0]
        
        return name
    
    def image_load(self, np_array):
        
        query = "SELECT image FROM images where image='{}'".format(np_array)
        cur = self.db.cursor()
        cur.execute(query)
        file_name = cur.fetchone()[0]

        with self.zf.open(file_name) as f:
            buf = io.BytesIO(f.read())
            area = np.load(buf)

        return area
    
    def lat_regression(self, use_code, ax):
        
        percent_lst = []
        for key in self.combined_samp.keys():
            # load np array data
            arr = self.image_load(key)
            # mark one that matches use_code
            mask = np.isin(arr, use_code)
            # find the percentage 
            avg = mask.astype(int).mean() * 100
            
            percent_lst += [avg]
        
        tmp2 = percent_lst
        percent_lst = np.array(percent_lst).reshape(-1,1)
        
        lat_lst = np.array(list(self.combined_samp.values()))
        tmp1 = lat_lst
        lat_lst = lat_lst.reshape(-1,1)
        
        r = LinearRegression()
        r.fit(lat_lst, percent_lst)
        slope = float(r.coef_)
        intercept =  float(r.intercept_)
            
        if ax is not None:
            #ax.scatter(x = lat_lst, y = percent_lst)
            ax.scatter(x = tmp1, y = tmp2)
            y0 = ax.get_xlim()[0] * slope + intercept
            y1 = ax.get_xlim()[1] * slope + intercept
                
            plt.plot(ax.get_xlim(), (y0,y1))
            

        return slope, intercept
    
    def year_regression(self, city, use_code, ax):
        
        # find the data correspond to the city name
        for c in self.cities:
            if c[1] == city:
                target = c
                
        place_id = target[0] 
        
        query = "SELECT * FROM images where place_id = {}".format(place_id)
        cur = self.db.cursor()
        cur.execute(query)
        img_list = cur.fetchall()
        
        years = []
        percents = []
        
        #get the .npy files associated with it and their year
        for row in img_list:
            year = row[0]
            img = row[1]
            # load nparray data
            arr = self.image_load(img)
            # save year 
            years += [year]
            
            #  figure out the percent total of all of the codes passed
            points = []
            for code in use_code:
                mask = np.isin(arr, code)
                avg = mask.astype(int).mean() * 100
                points += [avg]
                
            # add all the percentage
            total = 0
            for p in points:
                total += p
                
            percents += [total]
        # scatter plot all the percents per year
        ax.scatter(x= years, y = percents)
        
        years = np.array(years).reshape(-1,1)
        percents = np.array(percents).reshape(-1,1)
        # perform linear regression
        r = LinearRegression()
        r.fit(years, percents)
        
        # extract slope and intercept
        slope = float(r.coef_)
        intercept =  float(r.intercept_)
        
        y0 = ax.get_xlim()[0] * slope + intercept
        y1 = ax.get_xlim()[1] * slope + intercept
        # plot the regression data
        plt.plot(ax.get_xlim(), (y0,y1))
        
        return slope, intercept
    
    
    
    
    
    def animate(self, name):
        fig = plt.figure(figsize = (8,8))
        
        query = "SELECT place_id FROM places where name = '{}'".format(name)
        cur = self.db.cursor()
        cur.execute(query)
        place_id = cur.fetchone()
        
        query = "SELECT year, image FROM images where place_id = {}".format(place_id[0])
        cur = self.db.cursor()
        cur.execute(query)
        file_list = cur.fetchall()
        
        
        def helper(file):
            
            ax = fig.gca()
            # set title with year
            ax.set_title(file[0], fontsize = 20)
            
            # open files and extract np array data
            with self.zf.open(file[1]) as f:
                buf = io.BytesIO(f.read())
                B = np.load(buf)
            
            plt.imshow(B, cmap=self.use_cmap, vmin=0, vmax=255)
        
        # run FuncAnimation per year
        anim = FuncAnimation(fig,helper,file_list,interval = 400)
        html = anim.to_html5_video()
        # close the figure
        plt.close(fig)
        return html
        
        
        
        
        
        
        
        
        
    
    
    
    
    