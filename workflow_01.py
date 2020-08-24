#####
####

import numpy as np
import xarray as xr
import rioxarray
import pandas as pd
import zipfile
import geopandas as gpd
import requests
from io import BytesIO
from zipfile import ZipFile
import shapefile
from shapely.geometry import shape, mapping
import osr
import py7zr


#url to webpage from
Country = input('Please enter 3 alpha letters of ISO code of country in capital letters ')
url = "https://biogeo.ucdavis.edu/data/gadm3.6/shp/gadm36_"+ Country+"_shp.zip"
print(url)



data = requests.get(url)
data


#downloading and openning zipfile. We only need the border of a country so we only need the first zipfile of shapefile which is
#known as gdam36_countryisocode_0

with ZipFile(BytesIO(data.content)) as files:
    filenames = [y for y in sorted(files.namelist()) for ending in ['0.dbf', '0.prj', '0.shp', '0.shx'] if y.endswith(ending)] 
    print(filenames)
    dbf, prj, shp, shx = [BytesIO(files.read(file)) for file in filenames]
    r = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)

proj4 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
attributes, geometry = [], []
field_names = [field[0] for field in r.fields[1:]]  
for row in r.shapeRecords():  
    geometry.append(shape(row.shape.__geo_interface__))  
    attributes.append(dict(zip(field_names, row.record)))  
    
gdf = gpd.GeoDataFrame(data = attributes, geometry = geometry, crs = proj4)
print(gdf.head())




#Downloading the Fraction of Land Cover from Zenodo

url = "https://zenodo.org/record/3730469/files/frac100_allyears.7z?download=1"
response = requests.get(url)
print(response)



#unzipping the Fraction of Land Cover
with py7zr.SevenZipFile(BytesIO(response.content), mode='r') as z:
    names = z.getnames()
 

#open the fraction of land cover 
for name in names:
    ds = xr.open_dataset(name)
ds


#calculating the fraction of forest land cover from the dataset; globaly
forestall =ds.fracCover_50 + ds.fracCover_60 + ds.fracCover_70 + ds.fracCover_80 + ds.fracCover_90 + ds.fracCover_100 + ds.fracCover_160 + ds.fracCover_170
forestall



#converting to datset and assigning the name of fraction to the data variable
Forest = forestall.to_dataset(name ='fraction')
Forest



#renaming long and lat to x and y and write a crs to the dataset 
Forest = Forest.sortby(Forest.lat)
Forest = Forest.rename_dims({"lon": "x", "lat": "y"})
Forest = Forest.rename_vars({"lon": "x", "lat": "y"})
Forest = Forest.rio.write_crs("epsg:4326")
Forest



#clipping the fraction of global forest dataset for the country of interest using the shapefile of country border
Country_forest = Forest.fraction.rio.clip(gdf.geometry.apply(mapping), gdf.crs, drop=True)
Country_forest



#converting the dataset to dataframe. FFCT is the fraction of forest for the country of interest
df = Country_forest.where(Country_forest>0).mean(dim = ["x", "y"]).to_dataframe(name = "FFCT")
df = df.drop('spatial_ref', 1)
df



# df.to_csv('FFCT.csv')



# dataframe.plot(x = 'year', y = 'FFCT', title = 'ForestFraction').get_figure().savefig('FFCT.png')
