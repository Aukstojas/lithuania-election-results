
from kedro.pipeline import Pipeline, node
from .nodes import scrape_node

def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=scrape_node,
                inputs=None,
                outputs='raw_scraped_data',
                name='scrape_data'
            )
        ]
    )