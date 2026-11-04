import json, sys
sys.path.append('e:/MiniProject/demo1')
from src.services.dashboard_service import DashboardService
print(json.dumps(DashboardService.get_instance().get_stats()))
