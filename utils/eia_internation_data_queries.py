import os
import requests
from typing import Optional, Union
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np

class eia_api_PC():
    def __init__(self,token: Optional[str] = None):
        self.token = token if token else os.getenv("EIA_TOKEN")
        self.base_url = "https://api.eia.gov/v2/"
        self.header = {"Accept": "*/*"}

    def get_response(
        self,
        url: str,
        headers: dict,
    ) -> pd.DataFrame:
        """Helper function to get the response from the EIA API and return it as a dataframe."""
        time.sleep(0.25)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        return pd.DataFrame(json_response["response"]["data"])

    
    def format_date(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Helper function to format date."""
        if "period" in df.columns:
            df = df.rename(columns={"period": "Date"})
            df = df.set_index("Date")

            # If the index is only yearly, add month and day
            if len(str(df.index[0])) == 4:
                df.index = pd.to_datetime(df.index.astype(str) + "-01-01")

            df.index = pd.to_datetime(df.index)
        return df
    
    def get_data_by_id(self,productId:Union[str,list],unit:str =None,regions:Union[str,list] = ["AFRC","ASOC","CSAM","EURA","EURO","MIDE","NOAM"],activities:Union[str,list] = ["12","7","2","33","34","8"]):
        base_query="https://api.eia.gov/v2/international/data/?frequency=annual&data[0]=value"

        if isinstance(regions,list):
            for region in regions:
                base_query = f"{base_query}&facets[countryRegionId][]={region}"
        elif isinstance(regions,str):
            base_query = f"{base_query}&facets[countryRegionId][]={regions}"
        
        if isinstance(activities,list):
            for activity in activities:
                base_query = f"{base_query}&facets[activityId][]={activity}"
        elif isinstance(activities,str):
            base_query = f"{base_query}&facets[activityId][]={activities}"

        if isinstance(productId,list):
            for id in productId:
                base_query = f"{base_query}&facets[productId][]={id}"
        elif isinstance(productId,str):
            base_query = f"{base_query}&facets[productId][]={productId}"
        
        if unit:
            base_query =f"{base_query}&facets[unit][]={unit}"
        base_query = f"{base_query}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"
        query = f"{base_query}&api_key={self.token}"
        response = requests.get(query)
        json_response = response.json()
        data = pd.DataFrame(json_response["response"]["data"])
        data = data.loc[data["dataFlagId"]!="2"]
        data["value"] = data["value"].astype(float)
        data["period"] = data["period"].astype(int)
        return data

def plot_by_region_and_type(data:pd.DataFrame,kind:str="line",region_dict:dict={"Africa":"Afrique","Asia & Oceania":"Asie et Océanie","Central & South America":"Amérique centrale et du Sud","Eurasia":"Eurasie","Europe":"Europe","Middle East":"Moyen-Orient","North America":"Amérique du Nord"}):
    array = np.array([[1,1,1],
                      [2,1,2],
                      [3,3,1],
                      [4,2,2],
                      [5,2,3],
                      [6,2,3],
                      [7,2,4],
                      [8,2,4],
                      [9,2,5],
                      [10,2,5],
                      [11,3,4],
                      [12,3,4],
                      [13,3,5],
                      [14,3,5],
                      [15,3,5]])
    size_array = pd.DataFrame(array,columns=["n_products","plot_height","plot_width"])
    regions = data["countryRegionName"].unique()
    products = data["productName"].unique()
    n_products = len(products)
    fig = plt.figure()
    plot_height = size_array.loc[size_array["n_products"]==n_products,"plot_height"].values[0]
    plot_width = size_array.loc[size_array["n_products"]==n_products,"plot_width"].values[0]
    legend = []
    for id,product in enumerate(products):
        ax = plt.subplot(plot_height,plot_width,id+1)
        data_to_plot:pd.DataFrame = data.loc[(data["productName"]==product)] 
        data_to_plot = data_to_plot.sort_values(by=["countryRegionName","period"])
        data_to_plot_pivot:pd.DataFrame = data_to_plot.pivot(index="period",columns="countryRegionName",values="value")
        data_to_plot_pivot = data_to_plot_pivot.rename(columns=region_dict)
        data_to_plot_pivot.plot(kind=kind,ax=ax)
        ax.set_xlabel(f"Year")
        ax.set_ylabel(f"{product} - [{data_to_plot.loc[data_to_plot.index[0],"unit"]}]")
        ax.legend(loc="upper left",bbox_to_anchor=(0,1.5),ncols=4)
        if id>0:
            ax.get_legend().remove()

if __name__=="__main__":
    api = eia_api_PC() 
    data_ses = api.get_data_by_id(["4701","4702"])