from agents.mysql_query_agent import MySQLQueryAgent
from agents.python_code_agent import PythonCodeAgent
from agents.pyspark_transformer_agent import PySparkTransformerAgent
from agents.code_reviewer_agent import CodeReviewerAgent
from agents.query_optimizer_agent import QueryOptimizerAgent
from agents.debug_assistant_agent import DebugAssistantAgent
from agents.code_explainer_agent import CodeExplainerAgent
from agents.natural_language_to_code_agent import NaturalLanguageToCodeAgent
from agents.code_commenter_agent import CodeCommenterAgent
from agents.syntax_validator_agent import SyntaxValidatorAgent
from agents.unit_test_writer_agent import UnitTestWriterAgent
from agents.schema_mapper_agent import SchemaMapperAgent
from agents.benchmark_agent import BenchmarkAgent

AGENT_MAP = {
    "mysql": MySQLQueryAgent(),
    "python": PythonCodeAgent(),
    "pyspark": PySparkTransformerAgent(),
    "review": CodeReviewerAgent(),
    "optimize": QueryOptimizerAgent(),
    "debug": DebugAssistantAgent(),
    "explain": CodeExplainerAgent(),
    "nl_to_code": NaturalLanguageToCodeAgent(),
    "comment": CodeCommenterAgent(),
    "validate": SyntaxValidatorAgent(),
    "test": UnitTestWriterAgent(),
    "schema": SchemaMapperAgent(),
    "benchmark": BenchmarkAgent(),
}
