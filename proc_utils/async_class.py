import concurrent.futures


class AsyncTask(object):
    def __init__(self, workers=4):
        self.workers = workers

    def run_tasks(self, async_task, param_dicts):
        """
        :param async_task:
            Reference of asynchronous task
        :param param_dicts:
            List of parameter dicts for each async_task
        :return:
            Randomly ordered list of returned results
        """
        # ProcessPoolExecutor is faster than ThreadPoolExecutor
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.workers
        ) as executor:
            futures = {
                executor.submit(
                    async_task, task_params
                ) for task_params in param_dicts
            }
            concurrent.futures.wait(futures)
        results = [obj.result() for obj in futures]
        return results
