import os
import datetime
from mongo_metrics import MongoMetrics

if __name__ == "__main__":
    m = MongoMetrics()

    now = datetime.datetime.now()
    dt = now.strftime('%d-%m-%Y')

    metrics = m.retrieve_user_metrics()
    #m.print_user_convo_details(metrics)
    m.write_user_convo_details(metrics, os.path.dirname(__file__) + '\\' + dt + '_user_metrics.json')