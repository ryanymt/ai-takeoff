import os
import sys
from pathlib import Path
from kfp import compiler

from google.cloud import aiplatform as vertex_ai

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import pipeline as custom_pipeline
from conf import vertex_config


if __name__ == "__main__":
    # Pipeline variables
    PIPELINE_DIR = os.path.join(os.curdir, "pipelines")
    p_path = Path(PIPELINE_DIR)
    if not p_path.exists():
        p_path.mkdir()
    PIPELINE_PACKAGE_PATH = f"{PIPELINE_DIR}/pipeline_{vertex_config.ID}.json"
    # compile the pipeline
    pipeline_compiler = compiler.Compiler()
    pipeline_compiler.compile(pipeline_func=custom_pipeline, package_path=PIPELINE_PACKAGE_PATH)
    # instantiate pipeline representation
    pipeline_job = vertex_ai.PipelineJob(
        display_name=vertex_config.PIPELINE_NAME,
        template_path=PIPELINE_PACKAGE_PATH,
        pipeline_root=vertex_config.PIPELINE_ROOT,
        enable_caching=False,
    )
    # submit the pipeline run (may take ~20 minutes for the first run)
    pipeline_job.run(sync=True)
