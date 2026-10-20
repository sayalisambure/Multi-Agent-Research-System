from langchain.tools import tool   # will use this as decorator
import requests # for scrapping we will need this
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os #for folder and file management
from dotenv import load_dotenv
load_dotenv()   #loading the env files i.e.,tavily
from rich import print        #to print in beter way

# 1st tool -- tavily api key

# firstly load ur tavily client

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

#for creating a tool we have to create a function

@tool          #to convert normal function to tool decorator
def web_search(query:str) -> str:     #we are getting str and we are gonna return a str
   """Search the web for recent and reliable information on a topic. Returns Titles, URLs and snippets"""
   #doc string telling a large language model what we are gonna do and what we have to extract
   results = tavily.search(query=query,max_results=5)      #call the tavily

   out = []

   for r in results['results']:
      out.append(  
         f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
      )
   return "\n----\n".join(out)

# we are running loop on result of results
# in which we have 5 lists 
# in each list we have title,url,snippet-content(we extracting 300 words as further anyway we are doing scraping using beautiful soul)
# we have list with multiple string we joining them into a single string using .join()

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"

# here we want to extract text
# we are using try and except in case if website dosen't hits
# then we sent url, timeout(open 1 url try to open for 8 sec if it doesn't open, let it go) , headers(website can block beautiful soap so it looks like actual user is try to peek)
# then we are saving response given by beautiful soap which will have raw html page(resp.text)
# next we will run loop on soap and and will decompose script, style, nav, footer
# return the soap text(separator=" "),3000 words

