import os
# from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END,add_messages
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage,ToolMessage
from  pydantic import BaseModel
# from langchain_community.tools.tavily_search import TavilySearchResults


from typing import TypedDict, List,Annotated
from langchain_google_genai import ChatGoogleGenerativeAI

model = ChatGoogleGenerativeAI(model='gemini-2.0-flash',api_key="AIzaSyDK1CNcAhSrM4qy3UVIXLu7J7Qk2U51Rug",disable_streaming=True)
stream_model = ChatGoogleGenerativeAI(model='gemini-2.0-flash',api_key="AIzaSyDK1CNcAhSrM4qy3UVIXLu7J7Qk2U51Rug")
# os.environ['GOOGLE_API_KEY'] = "AIzaSyDK1CNcAhSrM4qy3UVIXLu7J7Qk2U51Rug"
os.environ['TAVILY_API_KEY'] = "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"
# tavily = TavilySearchResults(max_results=4)

from tavily import TavilyClient

from langgraph.config import get_stream_writer

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# print(tavily.search(query='pm_modi',max_result=2)['results'][1]['content'])

# Set the conversation memory type.       ✅
# memory = SqliteSaver.from_conn_string(":memory:")
# Data structure of the agent state information
class State(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int
    messages:Annotated[List[str],add_messages]




PLAN_PROMPT = """You are an expert writer tasked with writing a report. \
Write a report for the user provided topic. Give an outline of the report along with any relevant notes \
or instructions for the sections."""

# WRITER_PROMPT = """You are a report assistant tasked with writing excellent reports.\
# Generate the best report possible for the user's request and the initial outline. \
# If the user provides critique, respond with a revised version of your previous attempts. \
# Use all the information below as needed: 
# ------ 
# {content}"""

WRITER_PROMPT = """You are an expert report writer. 
Generate a detailed, well-formatted report based on the user's request, using the outline and research content provided. 
Follow this structure exactly, using proper markdown formatting with bold section headings and bullet points where appropriate.

Structure:
1. Executive Summary
2. Introduction
3. Current Inflation Rates and Trends
4. Drivers of Inflation
5. Policy Responses
6. Impact of Inflation
7. Future Outlook and Risks
8. Conclusion
9. Appendix (Optional)

Incorporate all content and research provided, and maintain a clear, formal tone throughout the report.
------
Context and Research:
{content}
"""


REFLECTION_PROMPT = """You are a critic reviewing a report. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following report. Generate a list of search queries that will gather \
any relevant information. Only generate 3 queries max."""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""

# Queries list for the Tavily search tool
class Queries(BaseModel):
    queries: List[str]


# def plan_node(state:State):
#     messages = [
#         SystemMessage(content=PLAN_PROMPT),
#         HumanMessage(content=state['task'])
#     ]
#     print('plan node')
#     response = model.invoke(messages)
#     return {"plan": response.content }

from langgraph.config import get_stream_writer

def plan_node(state: State):
    writer = get_stream_writer()
    writer('plan node executing .....')
    try:
        task = state.get("task", "").strip()

    except:
        if not task:
            writer('provide infomation')
            raise ValueError("Task cannot be empty for the planner.")
    
    messages = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=task)
    ]
    response = model.invoke(messages)

    return {"plan": response.content ,
    # "messages":[AIMessage(content='planning complate')]
    }




def research_plan_node(state:State):
    writer = get_stream_writer()
    writer('research plan node executing .....')
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_PLAN_PROMPT),
        HumanMessage(content=state['task'])
    ])

    print('research plan node')
    
    content = state.get('content', [])
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content}




def generation_node(state: State):
    writer = get_stream_writer()
    writer('generating report.....')
    print('generating node')
    content = "\n\n".join(state['content'] or [])
    user_message = HumanMessage(
        content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
    messages = [
        SystemMessage(
            content=WRITER_PROMPT.format(content=content)
        ),
        user_message
        ]
    response=""
    # response = model.invoke(messages)
    for chunk in stream_model.stream(messages):
        print(chunk.content)
        if state.get("revision_number",1)==2:
            response+=chunk.content
            # writer(chunk.content)
            writer(response) # final streaming 
            #  print(chunk.content)
        response+=chunk.content


    return{
        "draft": response,
        "revision_number": state.get("revision_number", 1) + 1,
        # "messages":[AIMessage(content=f"generation node ......revise{state.get('revision_number',None)}")]
        }




def report_out(state:State):
    print('report submit')
    return {'messages':[AIMessage(content=state.get('draft',''))]}


def reflection_node(state:State):
    print('reflection_node executing')
    writer = get_stream_writer()
    writer('reflect on generate report .....')
    messages = [
        SystemMessage(content=REFLECTION_PROMPT),
        HumanMessage(content=state['draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content,
    # "messages":[AIMessage(content='reflect on generate report ....')]
    }

def research_critique_node(state:State):
    print('research critque node.....')
    writer = get_stream_writer()
    writer('critique by external source.....')
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state['critique'])
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content,
    # "messages":[AIMessage(content='research critique node ......')]
    }

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return "report_out"
    return "reflect"

# Initialise the graph with the agent state
builder = StateGraph(State)

# Add all the nodes (agents)
builder.add_node("planner", plan_node)
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.add_node("research_plan", research_plan_node)
builder.add_node("research_critique", research_critique_node)
builder.add_node('report_out',report_out)

# Set the starting agent
builder.set_entry_point("planner")

# Set the conditional edge
# This decides, whether to do another refinement loop, or to end
builder.add_conditional_edges(
    "generate", 
    should_continue, 
    {"reflect": "reflect","report_out":"report_out"}
)

# Agent workflow ("generate" is already covered by the conditional edge)
builder.add_edge("planner", "research_plan")
builder.add_edge("research_plan", "generate")

builder.add_edge("reflect", "research_critique")
builder.add_edge("research_critique", "generate")
builder.add_edge('report_out',END)

# Compile 
graph = builder.compile()





# Reactjs useStream hook to access final output of graph 

# //  console.log('refreshed')
#   const thread = useStream({
#     // apiUrl: "http://127.0.0.1:9090",
#     apiUrl: "http://127.0.0.1:9999",
#     assistantId: "agent",
#     messagesKey: "messages",

#     onFinish:(finalevent)=>{
#       setPartialResponse("")
#       // setFinalMessages(thread.messages); 

#       console.log(finalevent.values)    


 #    #  finalevent.values.state_key represent #

# content: ["# Report Writing: Overview The language of reports…o throughout your discussion or results sections.", "A report is written with a clear purpose and for a…shed sources referred to in your research report.", "World inflation rate for 2023 was 5.73%, a 2.2% de… 4.46% increase from 2021. · World inflation rate", "Global inflation is forecast to decline steadily, …ent in 2025, with advanced economies returning to", "The most recent factor estimates indicate that the…xtraordinarily expansionary demand conditions and", "The analysis suggests that fiscal policy played an…y contributed to inflation between 2021 and 2023.", "First, policy rules that respond forcefully to inf…n improve stability and reduce ELB-related risks.", "Why monetary policy should crack down harder durin…-dependent pricing”, CEPR Discussion Paper 19339.", "Global Impacts of the Ukraine War Two Years On | I…rests that European states held vis-a-vis Russia.", "The war in Ukraine has also resulted in significan…trading infrastructure, huge damage to production", …] (68)

# critique: "This is a good start to a comprehensive report on Russia! You've covered a lot of ground and touched upon key aspects of its history…"
# 
# draft: "``````markdown↵# Russia: A Comprehensive Overview↵↵## 1. Executive Summary↵↵Russia ismarkdown↵# Russia: A Comprehensive Overview↵↵## 1…"

# max_revisions: 2

# messages: [Object, Object, Object, Object, Object, Object, Object, Object, Object, Object, …] (14)

# plan: "Okay, I can create a report on Russia. Here's an outline and some notes to guide the writing process. This is designed to be …"
# 
# revision_number: 3

# task: "russia"
 

#       // console.log(finalevent.values.messages)
#       setFinalMessages(finalevent.values.messages); 
#       ; // clear partial
#       setUser("")
#       },
#     onCustomEvent: (event, options) => {
#        setPartialResponse(event)},    //for custom data stream by get_stream_writer
#     onError:(e)=>{console.log(e)}
#     // onCustomEvent: for custom event handler
    
#   });





# import pprint
# # Run it!
# thread = {"configurable": {"thread_id": "1"}}
# for s,m in graph.stream({
#     'task': "Write a report about the latest inflation figures in the European Union.",
#     "max_revisions": 2,
#     "revision_number": 1
# }, thread,stream_mode="messages"):
#     pprint.pprint(s.content)



