import azure.functions.mcp as mcp
print([name for name in dir(mcp) if not name.startswith('_')])
for name in dir(mcp):
    if 'Tool' in name or 'Context' in name or 'Mcp' in name:
        print(name, getattr(mcp, name))
