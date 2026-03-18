"""
OTel Effectiveness Test Suite

Structured test scenarios to exercise different chat patterns
and evaluate session quality via telemetry.

Run the tests manually in Copilot Chat, then analyze:
    py analyze_sessions.py otel-traces.jsonl

Each test describes:
  - What to send in chat
  - What to look for in telemetry
  - What "good" and "bad" signals look like
"""

TESTS = [
    # -----------------------------------------------------------------------
    # Category 1: Prompt clarity → response quality
    # -----------------------------------------------------------------------
    {
        "id": "CLEAR-1",
        "category": "Prompt Clarity",
        "name": "Clear, specific request",
        "prompt": "Write a Python function that returns the nth Fibonacci number using memoization. Include a docstring.",
        "expect": {
            "turns": 1,
            "tool_calls": 0,
            "signal": "Single turn, low tokens, fast completion = prompt was clear",
        },
    },
    {
        "id": "CLEAR-2",
        "category": "Prompt Clarity",
        "name": "Vague request (expect clarification or multiple turns)",
        "prompt": "Fix the code",
        "expect": {
            "turns": "1-2 (may ask clarification or attempt read_file)",
            "tool_calls": "Possibly file reads",
            "signal": "If >2 turns or canceled, prompt was too vague",
        },
    },
    {
        "id": "CLEAR-3",
        "category": "Prompt Clarity",
        "name": "Ambiguous multi-part request",
        "prompt": "Refactor main.py to add logging, error handling, and make it async",
        "expect": {
            "turns": "1-3",
            "tool_calls": "read_file, replace_string_in_file",
            "signal": "Multiple tool calls are fine here. High turns + repetition = agent confused by combined ask",
        },
    },

    # -----------------------------------------------------------------------
    # Category 2: Tool effectiveness
    # -----------------------------------------------------------------------
    {
        "id": "TOOL-1",
        "category": "Tool Effectiveness",
        "name": "Simple file read (built-in tool baseline)",
        "prompt": "Read main.py and explain what it does",
        "expect": {
            "turns": 1,
            "tool_calls": "1 read_file",
            "signal": "Exactly 1 tool call, low tokens. Baseline for tool efficiency.",
        },
    },
    {
        "id": "TOOL-2",
        "category": "Tool Effectiveness",
        "name": "Search task (multiple tool calls expected)",
        "prompt": "Find all Python files in this project and list them",
        "expect": {
            "turns": 1,
            "tool_calls": "1-2 (file_search or list_dir)",
            "signal": "Efficient = 1-2 calls. Inefficient = many calls scanning directories one by one.",
        },
    },
    {
        "id": "TOOL-3",
        "category": "Tool Effectiveness",
        "name": "Tool thrashing detector",
        "prompt": "Find where the variable 'result' is defined across the project",
        "expect": {
            "turns": "1-2",
            "tool_calls": "grep_search or semantic_search",
            "signal": "Watch for same tool called 3+ times with different params = search strategy is poor. Good = 1-2 targeted searches.",
        },
    },

    # -----------------------------------------------------------------------
    # Category 3: Azure SDK MCP server evaluation
    # Server: @azure/mcp (namespace mode), auth via Azure CLI
    # Tool names appear as mcp_azure-mcp_<namespace> in telemetry
    # -----------------------------------------------------------------------
    {
        "id": "MCP-1",
        "category": "Azure MCP — Tool Selection",
        "name": "Storage: list storage accounts (should trigger MCP)",
        "prompt": "List my Azure storage accounts",
        "expect": {
            "tool_calls": "mcp_azure-mcp_storage (or similar namespace tool)",
            "signal": "If MCP tool is NOT called → agent doesn't recognize this as an Azure task. If called correctly with results → tool selection works.",
        },
    },
    {
        "id": "MCP-2",
        "category": "Azure MCP — Tool Selection",
        "name": "Resource groups: list groups (should trigger MCP)",
        "prompt": "What resource groups exist in my Azure subscription?",
        "expect": {
            "tool_calls": "mcp_azure-mcp_group or mcp_azure-mcp_resources",
            "signal": "Clean single call = effective. Multiple retries = auth or tool issue.",
        },
    },
    {
        "id": "MCP-3",
        "category": "Azure MCP — Tool Selection",
        "name": "Negative test: non-Azure prompt should NOT invoke MCP",
        "prompt": "Write a Python function to sort a list of dictionaries by a key",
        "expect": {
            "tool_calls": "NO mcp_azure-mcp_* calls",
            "signal": "If Azure MCP is called here → tool descriptions are too broad, agent over-selects.",
        },
    },
    {
        "id": "MCP-4",
        "category": "Azure MCP — Tool Accuracy",
        "name": "Specific resource lookup",
        "prompt": "Show me details about my Azure subscription, including the subscription ID and tenant",
        "expect": {
            "tool_calls": "mcp_azure-mcp_subscription or mcp_azure-mcp_resources",
            "signal": "Response should match your known subscription (Azure SDK Developer Playground, tenant 72f988bf-...).",
        },
    },
    {
        "id": "MCP-5",
        "category": "Azure MCP — Error Handling",
        "name": "Query a service that may not exist",
        "prompt": "List my Azure Cosmos DB databases",
        "expect": {
            "tool_calls": "mcp_azure-mcp_cosmos",
            "signal": "If no Cosmos accounts exist, check: does the agent report 'none found' gracefully, or does it retry/error? Retries = poor error handling. Graceful empty = good.",
        },
    },
    {
        "id": "MCP-6",
        "category": "Azure MCP — Multi-tool Orchestration",
        "name": "Cross-service query requiring multiple MCP calls",
        "prompt": "List my resource groups and for each one, tell me how many storage accounts it contains",
        "expect": {
            "tool_calls": "Multiple mcp_azure-mcp_* calls (groups + storage)",
            "signal": "Watch turn count and tool call count. Efficient = 2-3 calls (list groups, then list storage per group or filtered). Inefficient = one call per resource group.",
        },
    },
    {
        "id": "MCP-7",
        "category": "Azure MCP — Ambiguity",
        "name": "Ambiguous Azure prompt (could map to multiple tools)",
        "prompt": "Show me what's in Azure",
        "expect": {
            "tool_calls": "Could be any mcp_azure-mcp_* tool",
            "signal": "Does the agent pick a reasonable starting point (resource groups? subscriptions?) or does it thrash across multiple namespaces? Focused selection = good tool descriptions.",
        },
    },
    {
        "id": "MCP-8",
        "category": "Azure MCP — Read-only Safety",
        "name": "Write operation should be blocked (if --read-only set)",
        "prompt": "Create a new resource group called otel-test-rg in East US",
        "instructions": "Only run this if you started the MCP server with --read-only flag.",
        "expect": {
            "signal": "If read-only mode is on, the MCP tool should return an error. Check if the agent reports this cleanly vs. retrying. If read-only is NOT on, the agent may actually create the resource — be careful.",
        },
    },

    # -----------------------------------------------------------------------
    # Category 4: Session-level patterns
    # -----------------------------------------------------------------------
    {
        "id": "SESS-1",
        "category": "Session Pattern",
        "name": "Single-shot success (ideal)",
        "prompt": "What is 2 + 2?",
        "expect": {
            "turns": 1,
            "tool_calls": 0,
            "signal": "Score should be ~100. Baseline for perfect efficiency.",
        },
    },
    {
        "id": "SESS-2",
        "category": "Session Pattern",
        "name": "Multi-turn agentic task",
        "prompt": "Create a new Python file called fibonacci.py with a function that computes Fibonacci, then write tests for it in test_fibonacci.py, then run the tests",
        "expect": {
            "turns": "3-6",
            "tool_calls": "create_file, run_in_terminal",
            "signal": "Turns are expected here. Score should still be decent if no thrashing. Watch for: repeated failed test runs (tool repetition), excessive file reads.",
        },
    },
    {
        "id": "SESS-3",
        "category": "Session Pattern",
        "name": "User cancellation (abandon signal)",
        "prompt": "Explain the entire history of computing in detail",
        "instructions": "Cancel the response mid-stream by clicking Stop.",
        "expect": {
            "signal": "copilot_chat.canceled=true. Heavy score penalty. High output tokens cut short. If users cancel often on similar prompts, the response style needs tuning.",
        },
    },

    # -----------------------------------------------------------------------
    # Category 5: Token efficiency
    # -----------------------------------------------------------------------
    {
        "id": "TOKEN-1",
        "category": "Token Efficiency",
        "name": "Concise answer expected",
        "prompt": "What Python version am I running? Just the version number.",
        "expect": {
            "signal": "Low input + low output = efficient. If output_tokens >> 100 for a version number, the agent is being verbose despite instruction.",
        },
    },
    {
        "id": "TOKEN-2",
        "category": "Token Efficiency",
        "name": "Large context, simple question",
        "prompt": "Does main.py have any imports?",
        "expect": {
            "signal": "Watch input_tokens. If the agent reads the whole file context exceeds 10K tokens for a 6-line file → context stuffing problem.",
        },
    },

    # -----------------------------------------------------------------------
    # Category 6: Model escalation
    # -----------------------------------------------------------------------
    {
        "id": "MODEL-1",
        "category": "Model Usage",
        "name": "Check which models are used per task type",
        "prompt": "Explain the difference between a list and a tuple in Python",
        "expect": {
            "signal": "Check gen_ai.request.model vs gen_ai.response.model. If a simple Q&A uses an expensive model (e.g., claude-opus-4-6), it may be over-provisioned. Look for gpt-4o-mini for lightweight tasks.",
        },
    },
]


def print_test_plan():
    """Print the test plan for manual execution."""
    categories = {}
    for test in TESTS:
        cat = test["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)

    for cat, tests in categories.items():
        print(f"\n{'=' * 70}")
        print(f"  {cat}")
        print(f"{'=' * 70}")
        for t in tests:
            print(f"\n  [{t['id']}] {t['name']}")
            print(f"  Prompt: \"{t['prompt']}\"")
            if "instructions" in t:
                print(f"  Instructions: {t['instructions']}")
            expect = t.get("expect", {})
            if "turns" in expect:
                print(f"  Expected turns: {expect['turns']}")
            if "tool_calls" in expect:
                print(f"  Expected tools: {expect['tool_calls']}")
            print(f"  Signal: {expect.get('signal', 'N/A')}")
    print()


if __name__ == "__main__":
    print_test_plan()
