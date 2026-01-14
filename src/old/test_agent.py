from crew import MSRTestMinerCrew

crew = MSRTestMinerCrew().crew()

# Simple test with one query
inputs = {"query": "test automation language:Python stars:>500"}

results = crew.kickoff(inputs=inputs)

print(f"Agent returned {len(results)} items")
print(results[:3])

