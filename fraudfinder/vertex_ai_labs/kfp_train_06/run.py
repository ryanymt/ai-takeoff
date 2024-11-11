import os
from kfp import compiler

from fraudfinder.vertex_ai_labs.kfp_train_06.pipeline import pipeline
from fraudfinder.vertex_ai_labs.kfp_train_06 import vertex_config


if __name__ == "__main__":
    # Pipeline variables
    PIPELINE_DIR = os.path.join(os.curdir, "pipelines")
    PIPELINE_PACKAGE_PATH = f"{PIPELINE_DIR}/pipeline_{vertex_config.ID}.json"
    # compile the pipeline
    pipeline_compiler = compiler.Compiler()
    pipeline_compiler.compile(pipeline_func=pipeline, package_path=PIPELINE_PACKAGE_PATH)
    # instantiate pipeline representation
    pipeline_job = vertex_ai.PipelineJob(
        display_name=vertex_config.PIPELINE_NAME,
        template_path=PIPELINE_PACKAGE_PATH,
        pipeline_root=vertex_config.PIPELINE_ROOT,
        enable_caching=False,
    )
    # submit the pipeline run (may take ~20 minutes for the first run)
    pipeline_job.run(sync=True)
