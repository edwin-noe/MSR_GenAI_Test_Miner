## Project Workflow
```
+-------------------+
| Generate Queries  | --docker--> queries.txt
+-------------------+
          |
          v
+-------------------+
| CrewAI Agent      | --explore--> GitHub Repos
+-------------------+
          |
          v
+-------------------+
| Repository Data   | --analyze--> MSR Study
+-------------------+
```

## **Requirements**

- [Docker](https://www.docker.com/get-started) installed on your machine  
- (Optional) GitHub Personal Access Token for authenticated API queries

---

## **Clone the Repository**
```
git clone git@github.com:edwin-noe/MSR_GenAI_Test_Miner.git
cd MSR_GenAI_Test_Miner
```

## Build the docker image
```
docker build -t msr_genai_test_miner .
```

## Run the project in Docker
```
docker run --rm -it \
  -v $(pwd):/app \
  msr_genai_test_miner \
  python generate_queries.py

# To save queries to a file
docker run --rm -it \
  -v $(pwd):/app \
  msr_genai_test_miner \
  python generate_queries.py > queries.txt
```

## Use GitHub API
```
docker run --rm -it \
  -v $(pwd):/app \
  -e GITHUB_TOKEN="your_token_here" \
  msr_genai_test_miner \
  python fetch_github_data.py
```

## Contributing
1. Fork the repo
2. Create a new branch: git checkout -b feature/your-feature
3. Make changes and commit: git commit -m "Add feature"
4. Push to your branch: git push origin feature/your-feature
5. Open a Pull Request

## Documentation
[CrewAI Documentation](https://docs.crewai.com/en/introduction)

## API Reference
[CrewAI API Reference](https://docs.crewai.com/en/api-reference/introduction)






