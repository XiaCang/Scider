import os; from dotenv import load_dotenv; load_dotenv()
from app.tasks.llm_tasks import extract_key_points_task

task = extract_key_points_task.delay(
    'test-paper-id-001',
    'This paper proposes a new graph neural network for citation recommendation...'
)
print('Task ID:', task.id)

import time; time.sleep(15)
print('State:', task.state)
print('Result:', task.result)