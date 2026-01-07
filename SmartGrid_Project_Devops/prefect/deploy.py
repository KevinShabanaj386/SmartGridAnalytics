"""
Prefect Deployment Configuration
Deploy Prefect flows për Smart Grid Analytics
"""
from prefect import serve
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule
from flows.smartgrid_etl_flow import smartgrid_etl_flow

# Krijo deployment për ETL flow
deployment = Deployment.build_from_flow(
    flow=smartgrid_etl_flow,
    name="smartgrid-etl-deployment",
    work_queue_name="smartgrid-etl-queue",
    schedule=CronSchedule(cron="0 * * * *", timezone="UTC"),  # Çdo orë
    tags=["smartgrid", "etl", "production"],
    parameters={
        "enable_validation": True,
        "enable_cleanup": False  # Cleanup vetëm një herë në ditë
    }
)

if __name__ == "__main__":
    # Deploy flow
    deployment.apply()
    print("✅ Deployment created successfully")

