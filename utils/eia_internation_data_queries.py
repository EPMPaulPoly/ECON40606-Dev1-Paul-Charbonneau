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
    
    def get_data_by_id(self,productId:Union[str,list],unit:str =None):
        base_query="https://api.eia.gov/v2/international/data/?frequency=annual&data[0]=value&facets[countryRegionTypeId][]=r&facets[countryRegionId][]=AFRC&facets[countryRegionId][]=ASOC&facets[countryRegionId][]=CSAM&facets[countryRegionId][]=EURA&facets[countryRegionId][]=EURO&facets[countryRegionId][]=MIDE&facets[countryRegionId][]=NOAM"
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
        data["value"] = data["value"].astype(float)
        data["period"] = data["period"].astype(int)
        return data

def plot_by_region_and_type(data:pd.DataFrame,kind:str):
    array = np.array([[1,1,1],
                      [2,1,2],
                      [3,3,1],
                      [4,2,2],
                      [5,3,2],
                      [6,3,2]])
    size_array = pd.DataFrame(array,columns=["n_products","plot_height","plot_width"])
    regions = data["countryRegionId"].unique()
    products = data["productName"].unique()
    n_products = len(products)
    fig = plt.figure()
    plot_height = size_array.loc[size_array["n_products"]==n_products,"plot_height"].values[0]
    plot_width = size_array.loc[size_array["n_products"]==n_products,"plot_width"].values[0]
    legend = []
    for id,product in enumerate(products):
        ax = plt.subplot(plot_height,plot_width,id+1)
        for region in regions:
            data_to_plot = data.loc[(data["countryRegionId"] ==region) & (data["productName"]==product)] 
            data_to_plot.plot(x="period",y="value",ax=ax,kind=kind)
            legend.append(region)
        ax.legend(legend)
        ax.set_xlabel(f"Year")
        ax.set_ylabel(f"{product} - [{data_to_plot.loc[data_to_plot.index[0],"unitName"]}]")

if __name__=="__main__":
    api = eia_api_PC() 
    data_ses = api.get_data_by_id(["4701","4702"])