from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser

# Create prompt template for summarizing social media posts
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at analyzing social media discussions about cryptocurrency tokens. 
    Your task is to create a clear, concise summary of all social media messages about a token.
    Focus on key themes, sentiment, and important discussions while maintaining accuracy.
    
    For each post, you'll receive detailed information including:
    - Source platform (e.g. warpcast, twitter)
    - Author's display name and username
    - Post content
    - Timestamp
    - Engagement metrics (reactions, replies, reposts)
    
    Include relevant engagement metrics and author information in your summary when they add context."""),
    ("user", """Here are social media posts about a token. Each post includes the platform source, author details, content, timestamp, and engagement metrics. Please provide a comprehensive summary:
    {posts}""")
])

llm = ChatOpenAI(temperature=0.1, model="gpt-4o", streaming=True, name='social_summary_llm')
# Create the chain
# Extract the text content from the AIMessage
social_summary_chain = (prompt | llm | StrOutputParser()).with_config({"run_name": "Social Summary"})
