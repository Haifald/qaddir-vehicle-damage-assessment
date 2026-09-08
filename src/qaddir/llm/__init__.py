"""LLM component: prompt construction, model calls, report generation.

The LLM consumes only the structured CV output. Any fact it states must trace
back to a field in that payload; see docs/llm_design.md once TASK-24 is done.
"""
