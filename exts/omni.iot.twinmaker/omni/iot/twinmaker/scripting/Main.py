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


def get_state() -> GameState:
    global _state
    return _state

class Main(BehaviorScript):
    def get_state(self):
        global _state
        return _state

    def on_init(self):
        carb.log_info(f"{__class__.__name__}.on_init()->{self.prim_path}")

    def on_destroy(self):
        global _state
        _state = None
        carb.log_info(f"{__class__.__name__}.on_destroy()->{self.prim_path}")

    def on_play(self):
        global _state
        if not _state:
            carb.log_info('create game state')
            _state = GameState()

        self.get_state().start()
        carb.log_info(f"{__class__.__name__}.on_play()->{self.prim_path} - {self.get_state().is_play}")

    def on_pause(self):
        self.get_state().pause()
        carb.log_info(f"{__class__.__name__}.on_pause()->{self.prim_path}")

    def on_stop(self):
        self.get_state().stop()
        carb.log_info(f"{__class__.__name__}.on_stop()->{self.prim_path}")

    def on_update(self, current_time: float, delta_time: float):
        #carb.log_info(f"{__class__.__name__}.on_update()->{self.prim_path}")
        pass