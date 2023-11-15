from  concurrent.futures import ThreadPoolExecutor
from omni.kit.scripting import BehaviorScript
import carb.events

class GameState(object):
    def __init__(self) -> None:
        self.is_play = False

    def start(self):
        self.is_play = True

    def pause(self):
        self.is_play = False

    def stop(self):
        self.is_play = False


_state = None
_executor = None


def get_state() -> GameState:
    global _state
    return _state

def get_executor():
    global _executor
    return _executor


class Main(BehaviorScript):
    def get_state(self):
        global _state
        return _state

    def on_init(self):
        global _state
        if not _state:
            _state = GameState()
        global _executor
        if not _executor:
            _executor = ThreadPoolExecutor(max_workers=4)
        carb.log_info(f"{__class__.__name__}.on_init()->{self.prim_path}")

    def on_destroy(self):
        global _state
        _state = None
        carb.log_info(f"{__class__.__name__}.on_destroy()->{self.prim_path}")

    def on_play(self):
        self.get_state().start()
        carb.log_info(f"{__class__.__name__}.on_play()->{self.prim_path}")

    def on_pause(self):
        self.get_state().pause()
        carb.log_info(f"{__class__.__name__}.on_pause()->{self.prim_path}")

    def on_stop(self):
        self.get_state().stop()
        carb.log_info(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        pass
