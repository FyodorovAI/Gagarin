import pytest
from models.agent import AgentModel, Rag, Tools
from pydantic import ValidationError

def get_default_agent(
        provider: str = "openapi",
        model: str = "gpt-3.5-turbo",
        name_for_human: str = "My Agent",
        description_for_human: str = "My Agent",
        prompt: str = "My Prompt",
        prompt_size: int = 1000,
        rag: [Rag] = [],
        tools: [Tools] = [],
    ) -> AgentModel:

    try:
        agent = AgentModel(
            provider=provider,
            model=model,
            name_for_human=name_for_human,
            description_for_human=description_for_human,
            prompt=prompt,
            prompt_size=prompt_size,
            rag=rag,
            tools=tools,
        )
    except ValidationError as e:
        print("Agent model validation error:", e)
        raise
    else:
        print("Agent model:", agent)
        return agent

def test_default_agent_validation():
    # Get an agent by calling get_default_agent()
    agent = get_default_agent()

    # Validate the agent and get a boolean indicating if it is valid
    is_valid = agent.validate()

    assert is_valid, (
        "Default agent should be valid"
    )


def test_long_name_for_human():
    # Create an agent with a long name for human
    long_name_agent = get_default_agent(name_for_human="A" * 101)
    is_valid = long_name_agent.validate()
    assert not is_valid, "Long name for human should result in an invalid agent"


def test_invalid_name_for_human():
    # Create an agent with an invalid name for human
    invalid_name_agent = get_default_agent(name_for_human="My Agent @!")
    is_valid = invalid_name_agent.validate()
    assert not is_valid, "Invalid name for human should result in an invalid agent"


def test_long_description_for_human():
    # Create an agent with a long description for human
    long_description_agent = get_default_agent(description_for_human="A" * 1001)
    is_valid = long_description_agent.validate()
    assert not is_valid, "Long description for human should result in an invalid agent"


def test_invalid_description_for_human():
    # Create an agent with an invalid description for human
    invalid_description_agent = get_default_agent(description_for_human="This is my agent @!")
    is_valid = invalid_description_agent.validate()
    assert not is_valid, "Invalid description for human should result in an invalid agent"


def test_invalid_api_url():
    try:
        # Create an agent with an invalid api_url
        invalid_url_agent = get_default_agent(api_url="invalid-url")
    except ValidationError as e:
        assert isinstance(e, ValidationError), "Expected a Pydantic ValidationError"
    else:
        assert False, "Expected a Pydantic ValidationError"
