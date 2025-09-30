import json
import redis
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class QueueService:
    """
    Serviço para enfileirar jobs no BullMQ via Redis
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD") or None,
            decode_responses=True
        )
        
    def add_kpi_job(
        self,
        sector: str,
        action: str = "calculate",
        data_id: Optional[int] = None,
        date_ref: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """
        Adiciona um job de cálculo de KPI na fila BullMQ
        """
        job_data = {
            "sector": sector,
            "action": action,
            "dataId": data_id,
            "dateRef": date_ref,
            "userId": user_id
        }
        
        # Remove valores None
        job_data = {k: v for k, v in job_data.items() if v is not None}
        
        # ID único do job
        job_id = f"{sector}-{action}-{data_id or 'batch'}"
        
        # Adiciona na fila do BullMQ
        queue_key = "bull:kpi-processing:wait"
        
        job_payload = {
            "name": "calculate-kpi",
            "data": job_data,
            "opts": {
                "jobId": job_id,
                "attempts": 3,
            }
        }
        
        # Adiciona o job na fila
        self.redis_client.lpush(queue_key, json.dumps(job_payload))
        
        print(f"📋 Job enfileirado: {job_id}")
        return job_id

# Instância global
queue_service = QueueService()
