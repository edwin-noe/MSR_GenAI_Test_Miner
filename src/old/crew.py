import os
import yaml
from crewai import Agent, Task, Crew

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../config")


class MSRTestMinerCrew:

    def __init__(self):
        self.agents_cfg = self.load_yaml("agents.yaml")
        self.tasks_cfg = self.load_yaml("tasks.yaml")

    def load_yaml(self, filename):
        with open(os.path.join(CONFIG_PATH, filename), "r") as f:
            return yaml.safe_load(f)

    def build_agents(self):
        github_explorer = Agent(
            name="GitHubExplorer",
            role=self.agents_cfg["GitHubExplorer"]["role"],
            goal=self.agents_cfg["GitHubExplorer"]["goal"],
            backstory=self.agents_cfg["GitHubExplorer"]["backstory"],
            verbose=True
        )

        test_analyst = Agent(
            name="TestAnalyst",
            role=self.agents_cfg["TestAnalyst"]["role"],
            goal=self.agents_cfg["TestAnalyst"]["goal"],
            backstory=self.agents_cfg["TestAnalyst"]["backstory"],
            verbose=True
        )

        return [github_explorer, test_analyst]

    def build_tasks(self):
        discovery = Task(
            name="repository_discovery",
            description=self.tasks_cfg["repository_discovery"]["description"],
            agent="GitHubExplorer",
            expected_output=self.tasks_cfg["repository_discovery"]["expected_output"]
        )

        screening = Task(
            name="qualitative_screening",
            description=self.tasks_cfg["qualitative_screening"]["description"],
            agent="TestAnalyst",
            expected_output=self.tasks_cfg["qualitative_screening"]["expected_output"]
        )

        return [discovery, screening]

    def crew(self):
        return Crew(
            agents=self.build_agents(),
            tasks=self.build_tasks(),
            process="sequential",
            verbose=True
        )
