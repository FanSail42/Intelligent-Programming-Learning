from app.services.material_pipeline import process_material
from app.tasks.celery_app import celery_app


@celery_app.task(name="material.process")
def process_material_task(material_id: int) -> None:
    process_material(material_id)
