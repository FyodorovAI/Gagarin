import pytest
from models.agent import AgentModel
from services.agent import Agent
from tests.test_agent_model import get_default_agent
from fyodorov_utils.config.config import Settings


@pytest.fixture
async def tool_fixture() -> tuple[AgentModel, str]:
    default_agent: AgentModel = get_default_agent()
    agent_id: str = Agent.create_in_db(default_agent)
    return default_agent, agent_id


@pytest.mark.asyncio
async def test_get_agent(agent_fixture):
    agent, agent_id = await agent_fixture
    fetched_agent = Agent.get_in_db(agent_id)
    assert fetched_agent["name_for_human"] == agent.name_for_human
    Agent.delete_in_db(agent_id)


@pytest.mark.asyncio
async def test_update_agent(agent_fixture):
    agent, agent_id = await agent_fixture
    update = agent.to_dict()
    update["description_for_human"] = "Updated description"
    updated_agent = Agent.update_in_db(agent_id, update)
    assert updated_agent["description_for_human"] == "Updated description"
    Agent.delete_in_db(agent_id)


@pytest.mark.asyncio
async def test_delete_agent(agent_fixture):
    _, agent_id = await agent_fixture
    deletion_result = Agent.delete_in_db(agent_id)
    assert deletion_result is True
