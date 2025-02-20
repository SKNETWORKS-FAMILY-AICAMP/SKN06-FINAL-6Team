import pandas as pd
import sqlite3

from langchain_community.document_loaders import DataFrameLoader
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()


## load
# 편스토랑
conn = sqlite3.connect("funs.db")
fdf = pd.read_sql("SELECT * FROM menu", conn)

fdf['page_content'] = fdf['name'] + " " + fdf['ingredients'] + " " + fdf['recipe']
fdf.drop(columns=['name', 'ingredients', 'recipe'], inplace=True)
conn.close()
loader = DataFrameLoader(fdf, page_content_column="page_content")
fdocs = loader.load()

# 냉장고를 부탁해
conn = sqlite3.connect("fridges.db")
rdf = pd.read_sql("SELECT * FROM menu", conn)

rdf['page_content'] = rdf['name'] + " " + rdf['ingredients'] + " " + rdf['recipes']
rdf.drop(columns=['name', 'ingredients', 'recipes'], inplace=True)
conn.close()
loader = DataFrameLoader(rdf, page_content_column="page_content")
rdocs = loader.load()

# 만개의 레시피
conn = sqlite3.connect("만개.db") # 이름 맞게 수정 필요
mdf = pd.read_sql("SELECT * FROM recipes", conn)

mdf['page_content'] = mdf['name'] + " " + mdf['ingredients'] + " " + mdf['recipe'] + " " + mdf['category']
mdf.drop(columns=['name', 'ingredients', 'recipes'], inplace=True)
conn.close()
loader = DataFrameLoader(mdf, page_content_column="page_content")
rdocs = loader.load()