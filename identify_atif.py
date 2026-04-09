"""Identify and analyze the ATIF sessions from Watson output."""
import json

for sid in ['48de0c87', 'fa32508d']:
    path = f'watson-output-vscode/{sid}/{sid}.atif.json'
    data = json.load(open(path, encoding='utf-8'))
    steps = data['steps']
    agent = data.get('agent', {})
    user_msgs = [s for s in steps if s.get('source') == 'user']
    first_user = user_msgs[0]['message'][:150] if user_msgs else '(none)'
    agent_steps = [s for s in steps if s.get('source') == 'agent']
    tool_steps = [s for s in steps if s.get('tool_calls')]
    
    total_in = sum(s.get('metrics', {}).get('prompt_tokens', 0) for s in steps)
    total_out = sum(s.get('metrics', {}).get('completion_tokens', 0) for s in steps)
    total_cached = sum(s.get('metrics', {}).get('cached_tokens', 0) for s in steps)
    
    print(f"Session: {sid}")
    print(f"  Agent: {agent.get('name', '?')} v{agent.get('version', '?')}")
    print(f"  Model: {agent.get('model_name', '?')}")
    print(f"  Steps: {len(steps)} (user={len(user_msgs)}, agent={len(agent_steps)}, with_tools={len(tool_steps)})")
    print(f"  First timestamp: {steps[0]['timestamp'] if steps else '?'}")
    print(f"  Last timestamp: {steps[-1]['timestamp'] if steps else '?'}")
    print(f"  Tokens: in={total_in:,} out={total_out:,} cached={total_cached:,}")
    print(f"  First user msg: {first_user}")
    print()
