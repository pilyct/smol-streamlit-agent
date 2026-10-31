from smolagents import ApiModel

def test_agent_builds_without_model_call():
    from doc_agent.agent import build_agent
    a = build_agent(verbose=0)

    assert a is not None
    assert hasattr(a, "tools")

    tool_names = set(a.tools) # a.tools is a dict keyed by tool name

    assert "search_documents" in tool_names
    assert "get_cached_summary" in tool_names
    assert "save_summary" in tool_names



def test_agent_does_not_retry_rate_limits():
    from doc_agent.agent import build_agent
    a = build_agent(verbose=0)

    assert isinstance(a.model, ApiModel)
    assert a.model.retryer.max_attempts == 1
