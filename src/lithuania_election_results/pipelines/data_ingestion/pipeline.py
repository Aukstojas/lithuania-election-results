
from .nodes import scrape_node
from kedro.pipeline import Pipeline, pipeline, node

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=scrape_node,
                inputs="params:root_url",
                outputs='raw_scraped_data',
                name='scrape_data'
            )
        ]
    )