def test_agent_builds_without_model_call(monkeypatch):
    monkeypatch.setenv("HUGGINGFACEHUB_API_TOKEN", "hf_dummy_token")
    monkeypatch.setenv("MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

    from doc_agent.agent import build_agent
    a = build_agent(verbose=0)

    assert a is not None
    assert hasattr(a, "tools")

    tools = a.tools

    # smolagents versions differ: tools may be a dict or list
    if isinstance(tools, dict):
        tool_names = set(tools.keys())
    else:
        tool_names = set(getattr(t, "name", str(t)) for t in tools)

    assert "search_documents" in tool_names
    assert "get_cached_summary" in tool_names
    assert "save_summary" in tool_names

