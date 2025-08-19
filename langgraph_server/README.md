
project name : Research and report writing agent with tavily search tool

[1].how Research and report writing agent work :

At frontend use Reactjs useStream() hook to render messages
backend side

In this example, each of the 5 agents plays a different role:

1.plan
2.research_plan
3.generate
4.reflect
5.research_critique

The workflow of this example starts with the "plan" agent (1). This agent defines the task along with any relevant notes or instructions.

The "reseach_plan" agent (2) is then charged with providing information that can be used to write the report. This agent generates a list of search queries that gather relevant information using the Taviliy search tool. It does generate a maximum of 3 queries.

The "generate" agent (3) then writes the actual report. If this agent is called for the first time, then it writes the initial draft to be passed on to the "reflect" agent (4). If this agent is called in later iterations ("revisions"), it also incorporates the feedback provided by the following two agents (4 and 5). The number of revisions can be set in the main.py script with the max_revisions setting. The default value is 2, which means that the workflow just does 1 full revision loop (including agents 4 and 5).

After the "generate" agent (3), the workflow checks, if the maximum number of revisions (max_revisions), has been reached. If yes, then the answer from the "generate" agent (3) is considered final and the workflow gets terminated. If not, then the answer from the "generate" agent (3) is passed on to the "reflect" agent (4) for a loop that includes agents 4 and 5.

The "reflect" agent (4) then makes suggestions on how that the current report can be improved.

The "research_critique" agent (5) then provides additional search queries for the Tavily search tool to collect additional relevant information. It does generate a maximum of 3 queries.

After this, the "generate" agent (3) gets called again to write an improved version of the report that incorporates the additional suggestions and information.










