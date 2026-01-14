from tools import GitHubSearchTool

tool = GitHubSearchTool()

query = "test automation language:Python stars:>500"

results = tool.run(query)

print(f"Found {len(results)} repositories")
for r in results[:5]:  # show top 5
    print(r["full_name"], r["stargazers_count"], r["html_url"])
