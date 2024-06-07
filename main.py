import asyncio
import random
import uuid
from abc import ABC
from typing import Literal


class TrafficLight(ABC):

    def __init__(self, direction):
        self.id = str(uuid.uuid4())[:4]
        self._waiting_units_counter = 0
        self.view_direction: Literal['left', 'right', 'up', 'down'] = direction
        self.condition = None

    def __str__(self):
        return f"{self.__class__.__name__} {self.view_direction} {self.id}"

    @property
    def waiting_units_counter(self):
        return self._waiting_units_counter

    def push_unit(self):
        self._waiting_units_counter += 1

    def pop_unit(self):
        if self._waiting_units_counter > 0:
            self._waiting_units_counter -= 1
        assert self._waiting_units_counter >= 0

    async def camera_event_pushing(self, event_queue: asyncio.PriorityQueue):
        while True:
            waiting_units_count = int(self.waiting_units_counter)
            await asyncio.sleep(1)
            if waiting_units_count != self.waiting_units_counter:
                event_queue.put_nowait((1 / self.waiting_units_counter, self.id))
                print(f"{self} pushed CameraEvent with priority = {self.waiting_units_counter} to event queue")


class AutomobileTrafficLight(TrafficLight):
    def __init__(self, condition: Literal['green', 'yellow', 'red'] = 'red', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condition: Literal['green', 'yellow', 'red'] = condition


class PedestrianTrafficLight(TrafficLight):
    def __init__(self, sector, condition: Literal['green', 'red'] = 'red', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.condition: Literal['green', 'red'] = condition
        self.sector: Literal['I', 'II', 'III', 'IV'] = sector


def init_environment() -> list[TrafficLight]:
    traffic_lights: list = []

    for direction in ('left', 'right', 'up', 'down'):
        traffic_lights.append(AutomobileTrafficLight(direction=direction))

    for direction, sector in (('left', 'I'), ('left', 'IV'), ('right', 'II'), ('right', 'III'),
                              ('up', 'III'), ('up', 'IV'), ('down', 'I'), ('down', 'II')):
        traffic_lights.append(PedestrianTrafficLight(direction=direction, sector=sector))

    return traffic_lights


async def random_units_generator(choices: list[TrafficLight]) -> None:
    while True:
        await asyncio.sleep(1)
        choice = random.choice(choices)
        choice.push_unit()
        print(f'1 unit was added in to {choice} queue')


async def main():
    traffic_lights: list[TrafficLight] = init_environment()
    event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    await asyncio.gather(
        random_units_generator(choices=traffic_lights),
        *(traffic_light.camera_event_pushing(event_queue) for traffic_light in traffic_lights)
    )


if __name__ == '__main__':
    asyncio.run(main())
