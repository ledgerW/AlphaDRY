from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter

from chains.tavily_chain import retriever as web_retriever
from chains.query_chain import chain as query_chain
from chains.alpha_chain import chain as alpha_chain
from langchain_core.load import dumpd, dumps, load, loads
from langchain_community.retrievers import TavilySearchAPIRetriever
import os
import json
import re


short_retriever = TavilySearchAPIRetriever(name='web', k=3)


def sanitize_query(query):
    if not query:
        return ""
    # Remove or replace problematic characters
    query = re.sub(r'[\'"]', '', query)  # Remove quotes
    query = query.strip()  # Remove leading/trailing whitespace
    return query if query else ""


def get_query(x):
    return sanitize_query(x['query'])


def get_base_chain(retriever=web_retriever, name="Base Alpha Seeker"):
    return (
        RunnablePassthrough.assign(research=lambda x: "")
        | RunnablePassthrough.assign(query=query_chain)
        | RunnablePassthrough.assign(web = get_query | retriever)
        | {
          'token': itemgetter('token'),
          'research': lambda x: str(x['web'])
        }
        | alpha_chain
    ).with_config({"run_name": name})

base_seek_alpha = get_base_chain()
base_seek_alpha = base_seek_alpha.with_fallbacks([
  get_base_chain(retriever=short_retriever, name="Fallback Base Alpha Seeker")
  ])


def get_multi_hop_chain(retriever=web_retriever, name="Multi-Hop Alpha Seeker"):
    return (
        RunnablePassthrough.assign(research=lambda x: "")
        | RunnablePassthrough.assign(query=query_chain)
        | RunnablePassthrough.assign(web = get_query | retriever)
        | {
            'token': itemgetter('token'),
            'research': lambda x: str(x['web'])
          }
        | RunnablePassthrough.assign(query=query_chain)
        | RunnablePassthrough.assign(web = get_query | retriever)
        | {
            'token': itemgetter('token'),
            'research': lambda x: str(x['web'])
          }
        | alpha_chain
    ).with_config({"run_name": name})

multi_hop_seek_alpha = get_multi_hop_chain()
multi_hop_seek_alpha = multi_hop_seek_alpha.with_fallbacks([
  get_multi_hop_chain(retriever=short_retriever, name="Fallback Multi-Hop Alpha Seeker")
  ])
