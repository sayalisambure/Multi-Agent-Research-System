from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

# craete base function
def run_research_pipeline(topic:str) -> dict:
    state = {}

    # step 1-search agent working--tavily
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()  #calling agent
    #invoking it..get the msg
    search_result = search_agent.invoke({
        "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    #last index(-1) of msg contain output so extract its content and store it in state with a key named search_results
    state["search_results"] = search_result['messages'][-1].content

    print("\n search result ",state['search_results'])

#step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()  #calling
    #this scrapes the links and links are got from 1st agent and stored in state
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"  #sending last 800 lines of state that contains result
        )]
    })

    state['scraped_content'] = reader_result['messages'][-1].content

    print("\nscraped content: \n", state['scraped_content'])



# get structured output --- call 2 chains

#step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)


    # we have to give input topic and research...so to send these two, combine both agent results
    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    #call the chain
    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    #after invocking will get a structured report and saved in state with key report
    print("\n Final Report\n",state['report'])

    #critic report 

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    # only report is needed as input
    #invocking critic chain and saving feedback in state with key feedback
    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])

    return state

#calling pipeline.py

if __name__ == "__main__":
    topic = input("\n Enter a research topic : ")
    run_research_pipeline(topic)