
from .nodes import scrape_node
from kedro.pipeline import Pipeline, pipeline, node

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            node(
                func=scrape_node,
                inputs=["params:static_page_root", "params:apygarda_prefix", "params:apygarda_location", "params:apylinke_prefix","params:apylinke_pirm_prefix"],
                outputs='all_total_pirm_votes_by_apylinke',
                name='scrape_data'
            )
        ]
    )