import asyncio
import inspect
import time

from inspect import signature

import streamlit as st

from ice.agents import get_agent
from ice.agents import get_agents
from ice.agents.base import Agent


def select_agent_class():
    agent_name = st.selectbox(
        "Select agent", [agent.__name__ for agent in get_agents()]
    )
    agent_class = get_agent(agent_name)
    return agent_class


def select_agent_params(agent_class):
    # Introspect names and types of arguments to agent_class.__init__
    agent_args = agent_class.__init__.__code__.co_varnames[1:]

    # Get type for each arg to __init__ from function signature
    agent_args_types = [
        signature(agent_class.__init__).parameters[arg].annotation for arg in agent_args
    ]

    # Get default values for each arg to __init__ from function signature
    def get_default_value(arg):
        default = signature(agent_class.__init__).parameters[arg].default
        if default == inspect.Parameter.empty:
            return None
        return default

    agent_args_defaults = [get_default_value(arg) for arg in agent_args]

    # Show user a form to fill in agent parameters
    agent_arg_values = {}
    for (agent_arg, agent_arg_type, agent_arg_default) in zip(
        agent_args, agent_args_types, agent_args_defaults
    ):
        # If arg is <class 'str'>, show a text input
        if agent_arg_type == str:
            agent_arg_values[agent_arg] = st.text_input(agent_arg, agent_arg_default)
        # If arg is <class 'float'> or <class 'int'>, show a number input
        elif agent_arg_type == float or agent_arg_type == int:
            agent_arg_values[agent_arg] = st.number_input(agent_arg, agent_arg_default)
        # If arg is <class 'bool'>, show a checkbox
        elif agent_arg_type == bool:
            agent_arg_values[agent_arg] = st.checkbox(agent_arg, agent_arg_default)
        else:
            st.write(f"Using default {agent_arg_default} for argument {agent_arg}")
            agent_arg_values[agent_arg] = agent_arg_default

    return agent_arg_values


def select_agent_method():
    agent_methods = ["answer", "relevance", "predict", "classify"]
    agent_method = st.selectbox("Select agent method", agent_methods)
    return agent_method


def select_answer_params():
    max_tokens = int(st.number_input("Max tokens", value=100))
    prompt = st.text_area(
        "Enter question",
        value="""
Human: Hi!

Assistant:""",
        height=300,
    )
    return prompt, max_tokens


def call_agent_complete(agent: Agent, prompt: str, max_tokens: int):

    start_time = time.time()
    response = asyncio.run(agent.complete(prompt=prompt, max_tokens=max_tokens))
    elapsed = time.time() - start_time

    return response, elapsed


def main():

    # User selects agent type
    agent_class = select_agent_class()

    # User selects agent params
    agent_params = select_agent_params(agent_class)

    # Instantiate agent with user-provided parameters
    agent = agent_class(**agent_params)

    # User selects agent method to call
    agent_method = select_agent_method()
    if agent_method != "answer":
        # TODO: Implement other methods
        st.warning("Not implemented yet")
        st.exit()

    # User selects answer params
    prompt, max_tokens = select_answer_params()

    # Call agent method
    response, elapsed = call_agent_complete(agent, prompt, max_tokens)
    st.markdown(" > " + response)
    st.write(f"Response time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
