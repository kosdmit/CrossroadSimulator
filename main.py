import asyncio
import random
import uuid
from abc import ABC
from typing import Literal


TIK_TIME: int = 5


class TrafficLight(ABC):
    TRAFFIC_CAPACITY: int

    def __init__(self, direction, condition: Literal['green', 'red'] = 'red'):
        self.id = str(uuid.uuid4())[:4]
        self._waiting_units_counter = 0
        self.direction: Literal['left', 'right', 'up', 'down'] = direction
        self.group: Literal['vertical', 'horizontal'] = 'horizontal' if direction in ('left', 'right') else 'vertical'
        self.condition: Literal['green', 'red'] = condition

    def __str__(self):
        return f"{self.__class__.__name__} ({self.direction}) #{self.id}"

    @property
    def waiting_units_counter(self):
        return self._waiting_units_counter

    def push_units(self, count: int = 1):
        self._waiting_units_counter += count

    def pop_unit(self):
        if self._waiting_units_counter > 0:
            self._waiting_units_counter -= 1
        assert self._waiting_units_counter >= 0

    async def camera_event_pushing(self, event_queue: asyncio.PriorityQueue):
        """ Цикл работы камеры. Передает события о загруженности светофора в очередь. """
        while True:
            waiting_units_count = int(self.waiting_units_counter)
            await asyncio.sleep(TIK_TIME)
            if waiting_units_count != self.waiting_units_counter:
                try:
                    event_queue.put_nowait((1 / self.waiting_units_counter, self.id))
                except ZeroDivisionError:
                    pass
                else:
                    print(f"{self} pushed event with units count = {self.waiting_units_counter} to event queue "
                          f"(priority = {1 / self.waiting_units_counter})")

    async def work_cycle(self):
        """ Цикл работы светофора. Обеспечивает движение транспорта. """
        while True:
            await asyncio.sleep(TIK_TIME)
            if self.condition == 'green':
                for _ in range(self.TRAFFIC_CAPACITY):
                    self.pop_unit()
            print(f"{self} is {self.condition}. Waiting units: {self.waiting_units_counter}")


class AutomobileTrafficLight(TrafficLight):
    """ Автомобильный светофор """
    TRAFFIC_CAPACITY = 2


class PedestrianTrafficLight(TrafficLight):
    """ Пешеходный светофор """
    TRAFFIC_CAPACITY = 3

    def __init__(self, sector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sector: Literal['I', 'II', 'III', 'IV'] = sector

    def __str__(self):
        return f"{self.__class__.__name__} ({self.direction}, sector {self.sector}) #{self.id}"


def init_traffic_lights() -> dict[str, TrafficLight]:
    """ Инициализация светофоров """
    traffic_lights: dict = {}

    for direction in ('left', 'right', 'up', 'down'):
        automobile_traffic_light = AutomobileTrafficLight(direction=direction)
        traffic_lights[automobile_traffic_light.id] = automobile_traffic_light

    for direction, sector in (('left', 'I'), ('left', 'IV'), ('right', 'II'), ('right', 'III'),
                              ('up', 'III'), ('up', 'IV'), ('down', 'I'), ('down', 'II')):
        pedestrian_traffic_light = PedestrianTrafficLight(direction=direction, sector=sector)
        traffic_lights[pedestrian_traffic_light.id] = pedestrian_traffic_light

    return traffic_lights


async def random_units_generator(choices: list[TrafficLight]) -> None:
    """ Добавляет автомобили или пешеходов случайному светофору """
    while True:
        await asyncio.sleep(1)
        choice = random.choice(choices)
        choice.push_units(count=random.randint(1, 4))
        print(f'Units were added to {choice} queue')


async def traffic_light_control(event_queue: asyncio.PriorityQueue, traffic_lights) -> None:
    """ Выполняет переключения состояний светофоров в зависимости от приоритета в очереди """
    while True:
        await asyncio.sleep(TIK_TIME)
        event = await event_queue.get()
        most_loaded_traffic_light = traffic_lights[event[1]]
        for traffic_light in traffic_lights.values():
            if traffic_light.group == most_loaded_traffic_light.group:
                traffic_light.condition = 'green'
            else:
                traffic_light.condition = 'red'
        print(f"{most_loaded_traffic_light} turned green")


async def main():
    traffic_lights: dict[str, TrafficLight] = init_traffic_lights()
    event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()

    await asyncio.gather(
        random_units_generator(choices=list(traffic_lights.values())),
        traffic_light_control(event_queue, traffic_lights),
        *(traffic_light.work_cycle() for traffic_light in traffic_lights.values()),
        *(traffic_light.camera_event_pushing(event_queue) for traffic_light in traffic_lights.values())
    )


if __name__ == '__main__':
    asyncio.run(main())
