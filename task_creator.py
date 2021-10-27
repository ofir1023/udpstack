import asyncio


class TaskCreator:
    def __init__(self):
        self.tasks = []

    def create_task(self, coroutine):
        self.tasks.append(asyncio.create_task(coroutine))

    def __del__(self):
        # TODO: wait for tasks
        pass
